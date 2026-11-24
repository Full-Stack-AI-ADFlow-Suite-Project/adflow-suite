"""Il prompt delle immagini AI di rimpiazzo (spec R-43, brief-ai T3-34, T3-920).

Lo scrive il codice, non l'AI. Parte dalla scena dell'uscita (soggetto,
inquadratura, luce, colori) e, senza scena, dal tema; aggiunge l'attività (il
contesto visivo che l'AI del piano ricava dal profilo, ADR-125), la campagna, la
stagione e lo stile delle foto vere. Il file ``prompts/immagine_v4.md`` ha il
testo; la riga di stagione e quella di tono si tolgono nella versione semplice,
per la seconda prova dopo un rifiuto (R-35).
"""

from collections.abc import Mapping
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

VERSIONE_PROMPT = "immagine_v4"
_FILE = Path(__file__).parent / "prompts" / f"{VERSIONE_PROMPT}.md"
# Righe del prompt che la versione semplice non ha.
_RIGHE_FACOLTATIVE = ("{stagione}", "{tono}")
# Righe che mancano quando non c'è niente da dire.
_RIGHE_SE_MANCANO = (
    "{mondo_visivo}",
    "{gamma}",
    "{eventi}",
    "{campagna_titolo}",
    "{campagna_descrizione}",
    "{campagna_obiettivo}",
    "{inquadratura}",
    "{luce}",
    "{colori}",
    "{stile}",
    "{nota}",
    "{da_evitare}",
    "{da_non_mostrare}",
)
_MAX_TEMA = 200
_MAX_SCENA = 200
_MAX_CAMPO = 300
_MAX_CAMPAGNA = 500
_MAX_STILE = 400
# Quanto delle immagini già avute si passa al provider, in caratteri.
_MAX_DA_EVITARE = 1200

_STAGIONI = {
    12: "inverno",
    1: "inverno",
    2: "inverno",
    3: "primavera",
    4: "primavera",
    5: "primavera",
    6: "estate",
    7: "estate",
    8: "estate",
    9: "autunno",
    10: "autunno",
    11: "autunno",
}
_MESI = (
    "gennaio",
    "febbraio",
    "marzo",
    "aprile",
    "maggio",
    "giugno",
    "luglio",
    "agosto",
    "settembre",
    "ottobre",
    "novembre",
    "dicembre",
)
# Le sei inquadrature (T3-910, ADR-125) come si leggono in un prompt: valgono per
# ogni attività; che cosa ritraggono lo dice il soggetto della scena.
_INQUADRATURE = {
    "dettaglio": "dettaglio ravvicinato",
    "ambiente_interno": "l'ambiente interno, in campo largo",
    "ambiente_esterno": "l'esterno e i dintorni del luogo",
    "materie_prime": "le materie prime o gli ingredienti, accostati",
    "momento_d_uso": "un momento d'uso o di consumo, senza persone riconoscibili",
    "atmosfera_stagione": "l'atmosfera della stagione",
}
# Come si legge il tipo di prodotto del profilo in una frase.
_TIPI_PRODOTTO = {"alimentare": "prodotti alimentari"}


@lru_cache
def _testo() -> str:
    return _FILE.read_text(encoding="utf-8")


def _tipo_prodotto(valore: Any) -> str:
    """``ceramica_vetro`` come «ceramica e vetro»; senza tipo, prodotti artigianali."""
    if not isinstance(valore, str) or valore in ("", "altro"):
        return "prodotti artigianali"
    return _TIPI_PRODOTTO.get(valore, valore.replace("_", " e "))


def _attivita(snapshot: Mapping[str, Any], contesto: Mapping[str, Any]) -> str:
    """Che attività è: la frase del contesto visivo, o un ripiego dal profilo.

    Il ripiego serve alle campagne con un piano senza contesto (scritto prima
    di ADR-125): dice il tipo di prodotto e, se c'è, il nome.
    """
    scritta = _breve(contesto.get("attivita"), _MAX_CAMPO)
    if scritta:
        return scritta
    tipo = _tipo_prodotto(snapshot.get("tipo_prodotto"))
    nome = _breve(snapshot.get("nome"), _MAX_CAMPO)
    base = f"un'attività artigiana di {tipo}"
    return f"{nome}, {base}" if nome else base


def _breve(valore: Any, massimo: int) -> str:
    """Il testo su una riga, al massimo ``massimo`` caratteri; vuoto se non c'è.

    Un punto finale si toglie: il template lo rimette, così non se ne trovano due.
    """
    if not isinstance(valore, str):
        return ""
    testo = " ".join(valore.split())[:massimo]
    if testo.endswith("."):
        testo = testo[:-1].rstrip()
    return testo


def _eventi_del_periodo(snapshot: Mapping[str, Any], giorno: date) -> str:
    """I nomi degli eventi ricorrenti che cadono nel mese o nella stagione del post."""
    eventi = snapshot.get("eventi_ricorrenti")
    if not isinstance(eventi, list):
        return ""
    mese = _MESI[giorno.month - 1]
    stagione = _STAGIONI[giorno.month]
    nomi = []
    for evento in eventi:
        if not isinstance(evento, dict):
            continue
        nome = evento.get("nome")
        quando = evento.get("quando")
        if not isinstance(nome, str) or not isinstance(quando, str):
            continue
        quando = quando.lower()
        if mese in quando or stagione in quando:
            nomi.append(" ".join(nome.split()))
    return ", ".join(dict.fromkeys(nomi))


def prompt_immagine(
    snapshot: Mapping[str, Any],
    tema: str,
    giorno: date,
    *,
    semplice: bool = False,
    nota: str | None = None,
    da_evitare: tuple[str, ...] | list[str] = (),
    campagna: Mapping[str, Any] | None = None,
    scena: Mapping[str, Any] | None = None,
    stile: str | None = None,
    contesto: Mapping[str, Any] | None = None,
) -> str:
    """Il prompt dell'immagine di un'uscita.

    ``snapshot`` è la fotografia del profilo salvata all'invio; ``giorno`` è la
    data del post, che dà stagione ed eventi ricorrenti. Con ``scena`` il
    soggetto, l'inquadratura, la luce e i colori sono quelli dell'uscita
    (T3-910); senza, il soggetto è il ``tema``. ``contesto`` è il contesto
    visivo del piano, ``{"attivita", "mondo_visivo", "da_non_mostrare"}``
    (ADR-125); senza, l'attività si ricava dal profilo. ``campagna`` è
    ``{"titolo", "descrizione", "obiettivo"}``; ``stile`` è ciò che le
    descrizioni delle foto vere dicono di luce, sfondi e colori (T3-920).
    Con ``semplice`` mancano stagione e tono (R-35). ``nota`` è l'indicazione
    dell'operatore e ``da_evitare`` i prompt delle immagini che l'uscita ha
    già avuto (R-49).
    """
    citta = snapshot.get("citta")
    tono = snapshot.get("tono")
    indicazione = _breve(nota, _MAX_CAMPAGNA)
    evitare = " · ".join(_breve(uno, _MAX_CAMPO) for uno in da_evitare if uno)
    campagna = campagna or {}
    scena = scena or {}
    contesto = contesto or {}

    soggetto = _breve(scena.get("soggetto"), _MAX_SCENA) or _breve(tema, _MAX_TEMA)
    inquadratura = _breve(scena.get("inquadratura"), _MAX_CAMPO)
    if inquadratura:
        leggibile = _INQUADRATURE.get(inquadratura)
        if leggibile:
            inquadratura = f"{inquadratura} ({leggibile})"

    valori = {
        "attivita": _attivita(snapshot, contesto),
        "luogo": f" a {citta}" if isinstance(citta, str) and citta.strip() else "",
        "mondo_visivo": _breve(contesto.get("mondo_visivo"), _MAX_CAMPAGNA),
        "da_non_mostrare": _breve(contesto.get("da_non_mostrare"), _MAX_CAMPO),
        "gamma": _breve(snapshot.get("gamma"), _MAX_CAMPO),
        "eventi": _eventi_del_periodo(snapshot, giorno),
        "campagna_titolo": _breve(campagna.get("titolo"), _MAX_CAMPO),
        "campagna_descrizione": _breve(campagna.get("descrizione"), _MAX_CAMPAGNA),
        "campagna_obiettivo": _breve(campagna.get("obiettivo"), _MAX_CAMPO),
        "soggetto": soggetto,
        "inquadratura": inquadratura,
        "luce": _breve(scena.get("luce"), _MAX_CAMPO),
        "colori": _breve(scena.get("colori"), _MAX_CAMPO),
        "stagione": _STAGIONI[giorno.month],
        "tono": ", ".join(tono) if isinstance(tono, list) else "",
        "stile": _breve(stile, _MAX_STILE),
        "nota": indicazione,
        "da_evitare": evitare[:_MAX_DA_EVITARE],
    }
    righe = []
    for riga in _testo().strip().splitlines():
        if semplice and any(segno in riga for segno in _RIGHE_FACOLTATIVE):
            continue
        if "{tono}" in riga and not valori["tono"]:
            continue
        if any(
            segno in riga and not valori[segno.strip("{}")]
            for segno in _RIGHE_SE_MANCANO
        ):
            continue
        righe.append(riga.format(**valori))
    return "\n".join(righe)
