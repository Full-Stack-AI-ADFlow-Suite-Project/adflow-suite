"""Strumento di prova del ritocco (ADR-124, RT-32): ``python -m app.cli prova-ritocco``.

Carica le foto di una cartella (fuori dal repository) in una campagna di prova, la fa
generare (lo fa ``cli.py``, con il provider configurato) e poi, da qui:

- raccoglie per ogni foto le varianti, le note e i candidati;
- con un file di verità scritto a mano confronta riquadro del soggetto, angoli, volti e note;
- scrive il rapporto (token in ingresso, in uscita e in cache, costo per tipo di chiamata);
- scrive un foglio HTML di confronto con Originale, Standard e Spinta per ogni foto.

Con l'AI vera si lancia solo a mano (spende denaro); nei test girano l'AI e l'archivio finti.

Il file di verità è un JSON ``{"nome_foto.jpg": {...}}``; di ogni foto si scrive quello che si sa::

    {"soggetto": [x, y, larghezza, altezza],       # frazioni della foto, da 0 a 1
     "angoli": [[x, y], [x, y], [x, y], [x, y]],   # il quadrilatero principale, frazioni
     "volti": 2,                                   # quanti volti ci sono davvero
     "note": ["scura", "ruota_90"]}                # codici del catalogo
"""

from __future__ import annotations

import base64
import html
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from itertools import permutations
from math import hypot
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import leggi_impostazioni
from app.core.errori import DatiNonValidi
from app.core.orologio import ROMA
from app.moduli.accesso.models import Utente
from app.moduli.artigiani.models import ProfiloBottega
from app.moduli.campagne import service as campagne
from app.moduli.campagne.schemas import CampagnaCrea, GruppoCrea
from app.moduli.contenuti.schemas import RiepilogoAI

VARIANTI = ("originale", "standard", "spinta")
ESTENSIONI = {".jpg", ".jpeg", ".png", ".webp"}
CANALE_DI_PROVA = "instagram"
DURATA_GIORNI = 13


@dataclass
class EsitoCarica:
    """La campagna di prova: id, foto caricate (nome → id) e foto scartate con il motivo."""

    campagna_id: int
    caricate: dict[str, int] = field(default_factory=dict)
    scartate: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class FotoProva:
    """Quello che la prova sa di una foto dopo la generazione."""

    nome: str
    foto_id: int
    idonea: bool
    larghezza: int
    altezza: int
    note: list[str] = field(default_factory=list)
    avvisi: list[str] = field(default_factory=list)
    uguali: list[str] = field(default_factory=list)
    soggetto: dict[str, float] | None = None
    volti_trovati: int = 0
    quadrilateri: list[list[list[float]]] = field(default_factory=list)
    render: dict[str, bytes] = field(default_factory=dict)  # variante → JPEG


def carica_cartella(
    db: Session, cartella: Path, email: str, ora: datetime
) -> EsitoCarica:
    """Crea una campagna di prova per la bottega di ``email``, ci carica le foto e la invia.

    Le foto passano per ``campagne.carica_foto()``, con i suoi controlli: quelle che non li
    superano si scartano con il motivo. Si lanciano con la bottega di un artigiano già
    nel database (per esempio quello della demo); la campagna si chiama «prova ritocco».

    Raises:
        DatiNonValidi: la cartella o l'artigiano non ci sono, o nessuna foto è valida.
    """
    if not cartella.is_dir():
        raise DatiNonValidi(f"La cartella delle foto non esiste: {cartella}")
    utente = db.scalar(select(Utente).where(Utente.email == email))
    profilo = (
        db.scalar(select(ProfiloBottega).where(ProfiloBottega.utente_id == utente.id))
        if utente is not None
        else None
    )
    if profilo is None:
        raise DatiNonValidi(f"Non c'è la bottega dell'artigiano {email}.")
    anticipo = leggi_impostazioni().anticipo_minimo_giorni
    inizio: date = ora.astimezone(ROMA).date() + timedelta(days=anticipo + 1)
    nuova = campagne.crea_bozza(
        db,
        profilo.utente_id,
        CampagnaCrea(
            titolo="Prova ritocco",
            inizio=inizio,
            fine=inizio + timedelta(days=DURATA_GIORNI),
            descrizione="Foto di prova per il ritocco.",
            canali=list(profilo.canali),
        ),
        ora,
    )
    gruppo = campagne.crea_gruppo(
        db,
        profilo.utente_id,
        "artigiano",
        nuova.id,
        GruppoCrea(descrizione=f"Foto della cartella {cartella.name}"),
    )
    esito = EsitoCarica(campagna_id=nuova.id)
    percorsi = sorted(
        p for p in cartella.iterdir() if p.is_file() and p.suffix.lower() in ESTENSIONI
    )
    for percorso in percorsi:
        try:
            foto = campagne.carica_foto(
                db,
                profilo.utente_id,
                "artigiano",
                nuova.id,
                percorso.read_bytes(),
                gruppo.id,
            )
        except DatiNonValidi as errore:
            esito.scartate.append((percorso.name, errore.messaggio))
        else:
            esito.caricate[percorso.name] = foto.id
    if not esito.caricate:
        raise DatiNonValidi("Nessuna foto della cartella ha superato i controlli.")
    campagne.invia_campagna(db, profilo.utente_id, nuova.id, ora, dichiarazione=True)
    return esito


def raccogli(db: Session, nomi: dict[str, int]) -> list[FotoProva]:
    """Per ogni foto (nome → id) le varianti rese e quello che l'analisi ha trovato.

    Una foto non idonea o senza ritocco resta senza varianti rese: nel foglio c'è solo
    l'Originale.
    """
    fotografie = {f.id: f for f in campagne.foto_per_id(db, nomi.values())}
    risultato = []
    for nome, foto_id in nomi.items():
        foto = fotografie[foto_id]
        analisi = foto.analisi_ai if isinstance(foto.analisi_ai, dict) else {}
        ritocco = analisi.get("ritocco") or {}
        locale = analisi.get("locale") or {}
        candidati = locale.get("candidati") or {}
        ai = ritocco.get("ai") if isinstance(ritocco.get("ai"), dict) else {}
        privacy = ritocco.get("privacy") or []
        prova = FotoProva(
            nome=nome,
            foto_id=foto_id,
            idonea=analisi.get("idonea") is True,
            larghezza=foto.larghezza,
            altezza=foto.altezza,
            note=[n for n in ai.get("note") or [] if isinstance(n, str)],
            avvisi=list(ritocco.get("avvisi") or []),
            soggetto=(
                analisi.get("soggetto_box")
                if isinstance(analisi.get("soggetto_box"), dict)
                else None
            ),
            volti_trovati=sum(1 for z in privacy if z.get("ruolo") == "volto")
            or len(candidati.get("volti") or []),
            quadrilateri=[q["angoli"] for q in candidati.get("quadrilateri") or []],
        )
        disponibili, uguali = campagne.disponibilita_varianti(db, foto_id)
        prova.uguali = list(uguali)
        for variante in VARIANTI:
            if variante not in disponibili and variante != "originale":
                continue
            chiave = campagne.rendi_per_canale(
                db, foto_id, CANALE_DI_PROVA, {"variante": variante}
            )
            prova.render[variante] = campagne.leggi_render(foto_id, chiave)
        risultato.append(prova)
    return risultato


# --- Il confronto con la verità ------------------------------------------------------


def leggi_verita(percorso: Path) -> dict[str, dict[str, Any]]:
    """Il file di verità; un file illeggibile è un errore chiaro, non un'eccezione qualsiasi."""
    try:
        dati = json.loads(percorso.read_text(encoding="utf-8"))
    except (OSError, ValueError) as errore:
        raise DatiNonValidi(f"File di verità non leggibile: {errore}") from None
    if not isinstance(dati, dict) or not all(
        isinstance(v, dict) for v in dati.values()
    ):
        raise DatiNonValidi("Il file di verità è un oggetto «nome foto» → dati.")
    return dati


def sovrapposizione(a: dict[str, float], b: Iterable[float]) -> float:
    """Intersezione su unione (da 0 a 1) di due riquadri ``x, y, larghezza, altezza`` in frazioni."""
    bx, by, bw, bh = (float(v) for v in b)
    ax, ay, aw, ah = (float(a[k]) for k in ("x", "y", "larghezza", "altezza"))
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    comune = ix * iy
    unione = aw * ah + bw * bh - comune
    return comune / unione if unione > 0 else 0.0


def errore_angoli(
    trovati: list[list[float]], veri: list[list[float]], larghezza: int, altezza: int
) -> float:
    """Errore medio degli angoli, in % del lato lungo della foto; gli angoli si abbinano nel modo migliore."""
    lato = max(larghezza, altezza)
    migliore = None
    for ordine in permutations(range(4)):
        totale = sum(
            hypot(
                (trovati[i][0] - veri[k][0]) * larghezza,
                (trovati[i][1] - veri[k][1]) * altezza,
            )
            for k, i in enumerate(ordine)
        )
        migliore = totale if migliore is None else min(migliore, totale)
    return 100 * (migliore or 0.0) / 4 / lato


@dataclass
class ConfrontoVerita:
    """Quello che il confronto con la verità misura, su tutte le foto che hanno il dato."""

    riquadri: list[float] = field(default_factory=list)  # sovrapposizione per foto
    angoli: list[float] = field(default_factory=list)  # errore in % per foto
    volti_veri: int = 0
    volti_visti: int = 0
    accordo_note: list[float] = field(default_factory=list)  # intersezione su unione
    senza_candidato: list[str] = field(default_factory=list)


def confronta(
    foto: list[FotoProva], verita: dict[str, dict[str, Any]]
) -> ConfrontoVerita:
    """Mette a confronto quello che la prova ha trovato con quello che la persona ha scritto."""
    esito = ConfrontoVerita()
    for una in foto:
        vero = verita.get(una.nome)
        if not vero:
            continue
        if vero.get("soggetto") and una.soggetto:
            esito.riquadri.append(sovrapposizione(una.soggetto, vero["soggetto"]))
        if vero.get("angoli"):
            if una.quadrilateri:
                esito.angoli.append(
                    min(
                        errore_angoli(q, vero["angoli"], una.larghezza, una.altezza)
                        for q in una.quadrilateri
                    )
                )
            else:
                esito.senza_candidato.append(una.nome)
        if isinstance(vero.get("volti"), int):
            esito.volti_veri += vero["volti"]
            esito.volti_visti += min(una.volti_trovati, vero["volti"])
        if isinstance(vero.get("note"), list):
            veri, trovate = set(vero["note"]), set(una.note)
            unione = veri | trovate
            esito.accordo_note.append(
                len(veri & trovate) / len(unione) if unione else 1
            )
    return esito


# --- Il rapporto e il foglio -----------------------------------------------------------


def _dollari(valore: Decimal) -> str:
    return f"{valore:.4f} $"


def _media(valori: list[float]) -> str:
    return f"{sum(valori) / len(valori):.2f}" if valori else "-"


def rapporto(
    riepilogo: RiepilogoAI,
    foto: list[FotoProva],
    scartate: list[tuple[str, str]],
    confronto: ConfrontoVerita | None,
) -> str:
    """Il rapporto della prova: costi, cosa ha trovato l'analisi, confronto con la verità."""
    righe = [
        f"Prova ritocco · campagna {riepilogo.campagna_id}",
        f"  foto {len(foto)} ({sum(1 for f in foto if f.idonea)} idonee)"
        f" · scartate {len(scartate)}",
        "",
        "Chiamate per tipo",
        f"  {'tipo':<9}{'n':>4} {'token in':>10} {'in cache':>10} "
        f"{'token out':>10} {'costo':>12}",
    ]
    ingresso = in_cache = uscita = 0
    for riga in riepilogo.per_tipo:
        righe.append(
            f"  {riga.tipo:<9}{riga.chiamate:>4} {riga.token_ingresso:>10} "
            f"{riga.token_in_cache:>10} {riga.token_uscita:>10} "
            f"{_dollari(riga.costo_usd):>12}"
        )
        ingresso += riga.token_ingresso
        in_cache += riga.token_in_cache
        uscita += riga.token_uscita
    righe.append(
        f"  {'totale':<9}{'':>4} {ingresso:>10} {in_cache:>10} {uscita:>10} "
        f"{_dollari(riepilogo.costo_totale_usd):>12}"
    )
    if foto:
        righe.append(
            "  costo medio per foto: "
            + _dollari(riepilogo.costo_totale_usd / len(foto))
        )
    if ingresso:
        righe.append(
            f"  quota in cache: {100 * in_cache / ingresso:.1f}% dei token in ingresso"
        )
    righe += ["", "Foto"]
    for una in foto:
        uguali = (
            f" · uguali all'Originale: {', '.join(una.uguali)}" if una.uguali else ""
        )
        note = ", ".join(una.note) or "nessuna nota"
        righe.append(
            f"  {una.nome}: {'idonea' if una.idonea else 'NON idonea'}"
            f" · note: {note} · volti {una.volti_trovati}{uguali}"
        )
        righe.extend(f"    avviso: {a}" for a in una.avvisi)
    for nome, motivo in scartate:
        righe.append(f"  {nome}: scartata ({motivo})")
    if confronto is not None:
        righe += [
            "",
            "Confronto con la verità",
            f"  sovrapposizione del soggetto   {_media(confronto.riquadri)}"
            f" (su {len(confronto.riquadri)} foto, 1 = perfetta)",
            f"  errore degli angoli            {_media(confronto.angoli)} %"
            f" del lato lungo (su {len(confronto.angoli)} foto)",
        ]
        if confronto.senza_candidato:
            righe.append(
                "  senza quadrilatero trovato     "
                + ", ".join(confronto.senza_candidato)
            )
        richiamo = (
            f"{100 * confronto.volti_visti / confronto.volti_veri:.0f} %"
            if confronto.volti_veri
            else "-"
        )
        righe += [
            f"  richiamo dei volti             {richiamo}"
            f" ({confronto.volti_visti} su {confronto.volti_veri})",
            f"  accordo sulle note             {_media(confronto.accordo_note)}"
            f" (su {len(confronto.accordo_note)} foto, 1 = identiche)",
        ]
    return "\n".join(righe)


def foglio_html(foto: list[FotoProva]) -> str:
    """Il foglio di confronto: per ogni foto le sue varianti una accanto all'altra (immagini incorporate)."""
    blocchi = []
    for una in foto:
        celle = []
        for variante in VARIANTI:
            immagine = una.render.get(variante)
            if immagine is None:
                celle.append(
                    f"<figure><figcaption>{variante.capitalize()} · non disponibile"
                    "</figcaption></figure>"
                )
                continue
            dati = base64.b64encode(immagine).decode("ascii")
            uguale = " · uguale all'Originale" if variante in una.uguali else ""
            celle.append(
                f'<figure><img alt="{html.escape(una.nome)} · {variante}" '
                f'src="data:image/jpeg;base64,{dati}">'
                f"<figcaption>{variante.capitalize()}{uguale}</figcaption></figure>"
            )
        note = html.escape(", ".join(una.note + una.avvisi) or "nessuna nota")
        blocchi.append(
            f"<section><h2>{html.escape(una.nome)}</h2><p>{note}</p>"
            f'<div class="riga">{"".join(celle)}</div></section>'
        )
    return (
        '<!doctype html><html lang="it"><meta charset="utf-8">'
        "<title>Prova ritocco</title><style>"
        "body{font:14px system-ui;margin:1.5rem}.riga{display:flex;gap:1rem;flex-wrap:wrap}"
        "figure{margin:0;max-width:30%}img{max-width:100%;height:auto}"
        "</style><h1>Prova ritocco</h1>" + "".join(blocchi) + "</html>"
    )
