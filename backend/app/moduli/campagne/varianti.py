"""Le tre varianti di una foto, come comandi (ADR-124, RT-25, nota 12.5).

Dalla diagnosi (``diagnosi.diagnosi``) si ricavano **tre comandi** per l'esecutore:

- Originale: la foto come scattata, con le sole correzioni obbligatorie (rotazione di 90°,
  sRGB, rapporto con le regole di R-42, lato corto 1080). Nessun avvicinamento né luce;
- Standard: la prima modifica completa, con le dosi prudenti (``ritocco_catalogo.STANDARD``);
- Spinta: la stessa diagnosi con soglie e tetti più ampi (``ritocco_catalogo.SPINTA``).

I comandi sono dati puri e confrontabili: si sa prima di rendere che cosa cambia da una
variante all'altra. Se la Standard non cambia niente rispetto all'Originale, **è** il
comando dell'Originale (stessi byte in uscita); se la Spinta coincide con la Standard, la
card la spegne. Tutto si salva in ``foto.analisi_ai["ritocco"]`` (``ritocco_di_foto``).

La finestra si calcola qui (``finestra.calcola_finestra``) nella foto dopo i passi
geometrici: la geometria si simula su una copia piccola (stessa forma, nessun pixel vero),
con le stesse funzioni dell'esecutore.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Final

from PIL import Image

from app.core.errori import DatiNonValidi

from . import geometria
from . import ritocco_catalogo as catalogo
from .esecutore import Comando, RegoleR42, comando_originale
from .finestra import Finestra, calcola_finestra

LATO_SIMULAZIONE: Final[int] = 512
CANALE_PREDEFINITO: Final[str] = "instagram"


def _box(centesimi: list[int]) -> tuple[float, float, float, float]:
    x, y, w, h = centesimi
    return x / 100, y / 100, w / 100, h / 100


def _dict_box(centesimi: list[int]) -> dict[str, float]:
    x, y, w, h = _box(centesimi)
    return {"x": x, "y": y, "larghezza": w, "altezza": h}


def _simula_geometria(
    larghezza: int,
    altezza: int,
    ruota: int,
    raddrizza: dict[str, Any] | None,
    parametri: catalogo.Parametri,
) -> tuple[geometria.Mappa, tuple[int, int], dict[str, Any] | None]:
    """La mappa e le dimensioni vere dopo ruota e raddrizza; il raddrizza che regge ai controlli (o ``None``)."""
    scala = min(1.0, LATO_SIMULAZIONE / max(larghezza, altezza))
    proxy = Image.new(
        "L", (max(8, round(larghezza * scala)), max(8, round(altezza * scala)))
    )
    mappa = geometria.Mappa.identita(*proxy.size)
    proxy, mappa = geometria.ruota_90(proxy, ruota, mappa)
    effettivo = None
    if raddrizza and raddrizza.get("tipo") == "rotazione":
        gradi = float(raddrizza["gradi"])
        if catalogo.ROTAZIONE_MIN_GRADI <= abs(gradi) <= parametri.rotazione_max_gradi:
            proxy, mappa = geometria.raddrizza_rotazione(proxy, gradi, mappa)
            effettivo = {
                "tipo": "rotazione",
                "gradi": gradi,
                "max": parametri.rotazione_max_gradi,
            }
    elif raddrizza and raddrizza.get("tipo") == "prospettiva":
        esito = geometria.raddrizza_prospettiva(
            proxy, raddrizza["angoli"], mappa, parametri.prospettiva_deformazione_max
        )
        if esito is not None:
            proxy, mappa = esito
            effettivo = {
                "tipo": "prospettiva",
                "angoli": raddrizza["angoli"],
                "max": parametri.prospettiva_deformazione_max,
            }
    # le dimensioni vere: la copia piccola, riportata alla scala della foto
    return mappa, (round(proxy.width / scala), round(proxy.height / scala)), effettivo


def _luce(
    diag: dict[str, Any],
    parametri: catalogo.Parametri,
    soggetto: dict[str, float] | None,
) -> dict[str, Any] | None:
    d = diag["luce"]
    luce: dict[str, Any] = {}
    if d.get("esposizione"):
        luce["esposizione"] = {
            "verso": d["esposizione"],
            "tetto": parametri.esposizione_tetto_stop,
            "obiettivo": catalogo.ESPOSIZIONE_OBIETTIVO_L,
        }
    bianco = d.get("bianco")
    if bianco:
        if bianco.get("neutro"):
            luce["bianco"] = {
                "neutro": _dict_box(bianco["neutro"]),
                "tetto": parametri.bianco_tetto_canale,
            }
        elif parametri.bianco_senza_neutro_tetto > 0:
            luce["bianco"] = {
                "soggetto": True,
                "tetto": parametri.bianco_senza_neutro_tetto,
            }
    if d.get("ombre") and parametri.ombre_dose > 0:
        luce["ombre"] = parametri.ombre_dose
    if d.get("flash") and parametri.flash_dose > 0:
        luce["flash"] = parametri.flash_dose
    if not luce:
        return None
    if soggetto is not None:
        luce["soggetto"] = soggetto
    return luce


def _comando_modificato(
    larghezza: int,
    altezza: int,
    diag: dict[str, Any],
    soggetto: dict[str, float] | None,
    parametri: catalogo.Parametri,
) -> Comando:
    mappa, (w, h), raddrizza = _simula_geometria(
        larghezza, altezza, diag["ruota"], diag.get("raddrizza"), parametri
    )
    box_soggetto = mappa.box_norm(soggetto)
    centro = diag.get("centro")
    esito = calcola_finestra(
        w,
        h,
        soggetto=(
            (
                box_soggetto["x"],
                box_soggetto["y"],
                box_soggetto["larghezza"],
                box_soggetto["altezza"],
            )
            if box_soggetto
            else None
        ),
        tieni=[b for b in (_mappato(mappa, c) for c in diag["tieni"]) if b],
        togli=[b for b in (_mappato(mappa, c) for c in diag["togli"]) if b],
        centro=mappa.punto_norm(centro[0] / 100, centro[1] / 100) if centro else None,
        avvicina=diag["avvicina"],
        non_tagliare=diag["non_tagliare"],
        parametri=parametri,
        taglio_avvicinamento_max=parametri.ambiente_taglio_max
        if diag["ambiente"]
        else None,
    )
    return Comando(
        ruota=diag["ruota"],
        raddrizza=raddrizza,
        finestra=Finestra(esito.finestra.b, esito.finestra.rapporto),
        barre="sfocate" if esito.barre else None,
        luce=_luce(diag, parametri, soggetto),
        nitidezza=bool(diag["nitidezza"]),
        nitidezza_dose=parametri.nitidezza_dose,
    )


def _mappato(
    mappa: geometria.Mappa, centesimi: list[int]
) -> tuple[float, float, float, float] | None:
    box = mappa.box_norm(_dict_box(centesimi))
    return (box["x"], box["y"], box["larghezza"], box["altezza"]) if box else None


def _nessun_effetto(comando: Comando) -> bool:
    return comando.raddrizza is None and not comando.luce and not comando.nitidezza


def _soggetto_di(foto: Any) -> dict[str, float] | None:
    analisi = getattr(foto, "analisi_ai", None)
    box = analisi.get("soggetto_box") if isinstance(analisi, dict) else None
    return box if isinstance(box, dict) else None


def varianti(
    foto: Any, diag: dict[str, Any], locale: dict[str, Any] | None = None
) -> dict[str, Comando]:
    """I tre comandi ``originale``, ``standard`` e ``spinta`` di una foto.

    Le dimensioni vengono da ``locale["formato"]`` (già dritte per l'EXIF) o, senza, da
    ``foto.larghezza`` e ``foto.altezza``. Per uno screenshot o una grafica sono tutte e
    tre l'Originale.
    """
    formato = (locale or {}).get("formato") or {}
    larghezza = int(formato.get("larghezza") or foto.larghezza)
    altezza = int(formato.get("altezza") or foto.altezza)
    soggetto = _soggetto_di(foto)
    originale = comando_originale(foto, canale=CANALE_PREDEFINITO)
    if diag["ruota"]:
        originale = Comando(ruota=diag["ruota"], finestra=originale.finestra)
    if diag["solo_originale"]:
        return {"originale": originale, "standard": originale, "spinta": originale}

    comandi: dict[str, Comando] = {"originale": originale}
    for nome, parametri in catalogo.PARAMETRI_VARIANTE.items():
        comando = _comando_modificato(larghezza, altezza, diag, soggetto, parametri)
        if _nessun_effetto(comando):
            # Se la finestra è quella che darebbero le sole regole di R-42, è l'Originale.
            mappa, (w, h), _ = _simula_geometria(
                larghezza, altezza, diag["ruota"], None, parametri
            )
            semplice = calcola_finestra(
                w, h, soggetto=_mappato_dict(mappa, soggetto), parametri=parametri
            )
            if (
                Finestra(semplice.finestra.b, semplice.finestra.rapporto)
                == comando.finestra
                and (comando.barre == "sfocate") == semplice.barre
            ):
                comando = originale
        comandi[nome] = comando
    return comandi


def _mappato_dict(
    mappa: geometria.Mappa, box: dict[str, float] | None
) -> tuple[float, float, float, float] | None:
    mappato = mappa.box_norm(box)
    if mappato is None:
        return None
    return mappato["x"], mappato["y"], mappato["larghezza"], mappato["altezza"]


def uguali(comandi: dict[str, Comando]) -> dict[str, bool]:
    """``standard``: coincide con l'Originale; ``spinta``: coincide con la Standard."""
    return {
        "standard": comandi["standard"].a_dict() == comandi["originale"].a_dict(),
        "spinta": comandi["spinta"].a_dict() == comandi["standard"].a_dict(),
    }


def ritocco_di_foto(
    foto: Any, diag: dict[str, Any], locale: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Quello che si salva in ``foto.analisi_ai["ritocco"]``: i tre comandi, le uguaglianze e la diagnosi."""
    comandi = varianti(foto, diag, locale)
    return {
        "versione_esecutore": catalogo.VERSIONE_RITOCCO,
        "versione_diagnosi": diag["versione"],
        "varianti": {nome: c.a_dict() for nome, c in comandi.items()},
        "uguali": uguali(comandi),
        "privacy": diag["privacy"],
        "avvisi": diag["avvisi"],
        "scarti": diag["scarti"],
        "diagnosi": diag,
    }


# --- Lettura -----------------------------------------------------------------------


def _salvato(foto: Any) -> dict[str, Any] | None:
    analisi = getattr(foto, "analisi_ai", None)
    ritocco = analisi.get("ritocco") if isinstance(analisi, dict) else None
    if isinstance(ritocco, dict) and isinstance(ritocco.get("varianti"), dict):
        return ritocco
    return None


def disponibilita(foto: Any) -> tuple[list[str], list[str]]:
    """(varianti disponibili, varianti uguali alla precedente) per la card.

    Senza varianti salvate (foto non ancora analizzata o analizzata prima della corsia)
    c'è la sola Originale e la Standard le è uguale (D6): la Spinta è spenta.
    """
    salvato = _salvato(foto)
    if salvato is None:
        return ["originale", "standard"], ["standard"]
    segni = salvato.get("uguali") or {}
    disponibili = ["originale", "standard"]
    uguali_a_prima = []
    if segni.get("standard"):
        uguali_a_prima.append("standard")
    if segni.get("spinta"):
        uguali_a_prima.append("spinta")
    else:
        disponibili.append("spinta")
    return disponibili, uguali_a_prima


def comando_per_variante(foto: Any, canale: str, variante: str | None) -> Comando:
    """Il comando della variante per il canale; senza varianti salvate, l'Originale (D6).

    Raises:
        DatiNonValidi: variante sconosciuta o comando salvato non valido.
    """
    if variante not in (None, *catalogo.VARIANTI):
        raise DatiNonValidi("Variante della foto non valida.")
    salvato = _salvato(foto)
    if salvato is None:
        return comando_originale(foto, canale=canale)
    dati = salvato["varianti"].get(variante or "standard")
    if dati is None:
        return comando_originale(foto, canale=canale)
    comando = Comando.da_dict(dati)
    if isinstance(comando.finestra, RegoleR42):
        # l'intervallo dei rapporti è unico, ma il canale entra nella chiave del render
        comando = replace(comando, finestra=replace(comando.finestra, canale=canale))
    return comando
