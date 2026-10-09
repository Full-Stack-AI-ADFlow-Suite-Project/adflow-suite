"""Validatore a regole del testo di un post: funzione pura, a due livelli (R-09).

Un **blocco** rende il post `da_rivedere`; un **avviso** si salva e non ferma
nulla. I numeri vengono dalla scheda del canale (R-21, ``SCHEDE_CANALE``).

I blocchi scattano solo su ciò che è certo: una parola dell'elenco, un termine
che la bottega ha chiesto di non dire, un importo o un premio che i dati della
bottega non contengono. Il senso di una frase non si giudica qui: lo guardano
l'AI, che riceve la fotografia del profilo, e l'operatore in revisione.
"""

import re
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from .domain import LIVELLI_VALIDATORE, SCHEDE_CANALE

BLOCCO, AVVISO = LIVELLI_VALIDATORE

TESTO_VUOTO = "testo_vuoto"
LIMITE_CARATTERI = "limite_caratteri"
LIMITE_HASHTAG = "limite_hashtag"
PAROLE_VIETATE_REGOLA = "parole_vietate"
DA_NON_DIRE = "da_non_dire"
PREZZI_O_PREMI = "prezzi_o_premi"
MAX_CARATTERI = "max_caratteri"
MAX_HASHTAG = "max_hashtag"
REGOLE = {
    TESTO_VUOTO: BLOCCO,
    LIMITE_CARATTERI: BLOCCO,
    LIMITE_HASHTAG: BLOCCO,
    PAROLE_VIETATE_REGOLA: BLOCCO,
    DA_NON_DIRE: BLOCCO,
    PREZZI_O_PREMI: BLOCCO,
    MAX_CARATTERI: AVVISO,
    MAX_HASHTAG: AVVISO,
}

# Promesse che un post del consorzio non fa, per qualunque bottega.
PAROLE_VIETATE = (
    "gratis",
    "garantito",
    "miracoloso",
    "imbattibile",
    "il migliore",
    "numero uno",
)

# Come comincia, in `vincoli`, una frase che dice che cosa non dire.
_VERBI = r"(?:parlare|citare|dire|nominare|usare|menzionare|scrivere)"
_FORMULA = re.compile(
    rf"^(?:non\s+{_VERBI}|evitare(?:\s+di\s+{_VERBI})?|mai|niente|no)\b"
    # preposizioni e articoli che legano la formula al termine
    r"(?:\s+(?:(?:di|del|dello|della|dei|degli|delle|il|lo|la|i|gli|le)\b"
    r"|(?:dell|l|d)['’]))*\s*"
)
_PARTI_DEI_VINCOLI = re.compile(r"[;,.\n]+")
_MAX_PAROLE_DI_UN_TERMINE = 4

_IMPORTO = re.compile(
    r"(?:€\s*(\d[\d.,]*)|(\d[\d.,]*)\s*(?:€|euro\b|eur\b))", re.IGNORECASE
)
# Famiglie di parole che vantano un premio: valgono se la bottega lo dichiara.
_PREMI = {
    "premio": re.compile(r"(?<!\w)premi(?:o|ato|ata|ati|ate)(?!\w)"),
    "medaglia": re.compile(r"(?<!\w)medagli[ae](?!\w)"),
    "vincitore": re.compile(r"(?<!\w)vincit(?:ore|rice|ori|rici)(?!\w)"),
    "riconoscimento": re.compile(r"(?<!\w)riconosciment[oi](?!\w)"),
}


class ErroreDiValidazione(TypedDict):
    """Una voce di ``versione_post.errori_validazione`` (plan §2)."""

    livello: str
    regola: str
    messaggio: str


def _normalizza(testo: str) -> str:
    """Minuscole e senza accenti, per confrontare le parole."""
    scomposto = unicodedata.normalize("NFD", testo.lower())
    return "".join(c for c in scomposto if not unicodedata.combining(c))


def _schema(termine: str) -> re.Pattern[str]:
    """Il termine come parole intere, con l'ultima vocale libera.

    Così "sconti" trova anche "sconto" e "garantito" trova "garantita", senza
    arrivare a parole diverse che cominciano allo stesso modo.
    """
    pezzi = []
    for parola in _normalizza(termine).split():
        if len(parola) >= 4 and parola[-1] in "aeio":
            pezzi.append(re.escape(parola[:-1]) + "[aeio]")
        else:
            pezzi.append(re.escape(parola))
    return re.compile(r"(?<!\w)" + r"\s+".join(pezzi) + r"(?!\w)")


def termini_da_non_dire(vincoli: str | None) -> list[str]:
    """I termini che la bottega chiede di non dire, letti da ``vincoli``.

    Vale solo una frase che comincia con una formula come "non parlare di",
    "non citare", "evitare", "mai", ed è corta: "Non parlare di sconti" dà
    "sconti". Una frase più lunga o scritta in un altro modo non dà termini.
    """
    termini = []
    for parte in _PARTI_DEI_VINCOLI.split(_normalizza(vincoli or "")):
        parte = parte.strip()
        senza_formula = _FORMULA.sub("", parte, count=1).strip()
        if senza_formula == parte or len(senza_formula) < 3:
            continue
        if len(senza_formula.split()) > _MAX_PAROLE_DI_UN_TERMINE:
            continue
        if senza_formula not in termini:
            termini.append(senza_formula)
    return termini


def _testi(valore: Any) -> list[str]:
    """Tutti i testi dentro lo snapshot, a qualunque profondità."""
    if isinstance(valore, str):
        return [valore]
    if isinstance(valore, Mapping):
        return [testo for uno in valore.values() for testo in _testi(uno)]
    if isinstance(valore, (list, tuple)):
        return [testo for uno in valore for testo in _testi(uno)]
    return []


def _importi(testo: str) -> list[tuple[str, str]]:
    """Gli importi in euro del testo: (come è scritto, cifra da confrontare)."""
    trovati = []
    for trovato in _IMPORTO.finditer(testo):
        cifra = (trovato.group(1) or trovato.group(2)).rstrip(".,")
        trovati.append(
            (trovato.group(0).strip(), cifra.replace(".", "").replace(",", "."))
        )
    return trovati


def _errore(regola: str, messaggio: str) -> ErroreDiValidazione:
    return ErroreDiValidazione(
        livello=REGOLE[regola], regola=regola, messaggio=messaggio
    )


def valida_testo(
    testo: str,
    hashtag: Sequence[str],
    canale: str,
    snapshot: Mapping[str, Any] | None,
) -> list[ErroreDiValidazione]:
    """Blocchi e avvisi del testo di un post; elenco vuoto se non ce ne sono.

    Args:
        testo: il testo del post.
        hashtag: gli hashtag, senza ``#``.
        canale: il canale del post, per la sua scheda.
        snapshot: la fotografia del profilo salvata all'invio (R-11).

    Raises:
        ValueError: se il canale non ha una scheda.
    """
    if canale not in SCHEDE_CANALE:
        raise ValueError(f"Canale senza scheda: {canale}")
    scheda = SCHEDE_CANALE[canale]
    hashtag = list(hashtag)
    snapshot = snapshot or {}
    errori: list[ErroreDiValidazione] = []

    if not testo.strip():
        errori.append(_errore(TESTO_VUOTO, "Il testo è vuoto."))

    # Sulla piattaforma esce il testo con i suoi hashtag: il limite li conta.
    pubblicato = " ".join([testo] + [f"#{uno}" for uno in hashtag])
    if len(pubblicato) > scheda["limite_caratteri"]:
        messaggio = (
            f"Testo e hashtag sono {len(pubblicato)} caratteri: {canale} ne "
            f"accetta al massimo {scheda['limite_caratteri']}."
        )
        errori.append(_errore(LIMITE_CARATTERI, messaggio))
    if len(hashtag) > scheda["limite_hashtag"]:
        messaggio = (
            f"Gli hashtag sono {len(hashtag)}: {canale} ne accetta al massimo "
            f"{scheda['limite_hashtag']}."
        )
        errori.append(_errore(LIMITE_HASHTAG, messaggio))

    da_leggere = _normalizza(" ".join([testo] + hashtag))
    for parola in PAROLE_VIETATE:
        trovata = _schema(parola).search(da_leggere)
        if trovata:
            messaggio = f"Il testo contiene «{trovata.group(0)}», che non si usa."
            errori.append(_errore(PAROLE_VIETATE_REGOLA, messaggio))

    for termine in termini_da_non_dire(snapshot.get("vincoli")):
        trovato = _schema(termine).search(da_leggere)
        if trovato:
            messaggio = (
                f"Il testo contiene «{trovato.group(0)}», che la bottega ha "
                f"chiesto di non dire."
            )
            errori.append(_errore(DA_NON_DIRE, messaggio))

    della_bottega = _normalizza(" ".join(_testi(snapshot)))
    importi_della_bottega = {cifra for _, cifra in _importi(della_bottega)}
    for scritto, cifra in _importi(da_leggere):
        if cifra not in importi_della_bottega:
            messaggio = (
                f"Il testo indica un prezzo, «{scritto}», che non è nei dati "
                f"della bottega."
            )
            errori.append(_errore(PREZZI_O_PREMI, messaggio))
    for schema in _PREMI.values():
        trovato = schema.search(da_leggere)
        if trovato and not schema.search(della_bottega):
            messaggio = (
                f"Il testo parla di un premio, «{trovato.group(0)}», che non è "
                f"nei dati della bottega."
            )
            errori.append(_errore(PREZZI_O_PREMI, messaggio))

    # Limiti editoriali: solo se il limite della piattaforma è rispettato.
    if len(testo) > scheda["max_caratteri"] and LIMITE_CARATTERI not in {
        errore["regola"] for errore in errori
    }:
        messaggio = (
            f"Il testo è di {len(testo)} caratteri: su {canale} si consiglia "
            f"di restare entro {scheda['max_caratteri']}."
        )
        errori.append(_errore(MAX_CARATTERI, messaggio))
    if scheda["max_hashtag"] < len(hashtag) <= scheda["limite_hashtag"]:
        messaggio = (
            f"Gli hashtag sono {len(hashtag)}: su {canale} si consiglia di "
            f"restare entro {scheda['max_hashtag']}."
        )
        errori.append(_errore(MAX_HASHTAG, messaggio))

    return errori
