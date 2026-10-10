"""Limiti e controllo del piano di una campagna: funzioni pure, senza database.

I limiti dicono, per ogni canale, quanti post chiede la campagna e quali foto
ha a disposizione (R-05); il controllo dice se un piano scritto dall'AI li
rispetta (R-05, R-08, R-21, R-23, R-28). Nessuna funzione legge l'orologio o
la configurazione: periodo, ora e margine arrivano da chi chiama.

Gruppi e foto sono quelli di ``campagne.service.gruppi_della_campagna()``,
l'archivio è, canale per canale, l'elenco di
``campagne.service.foto_di_archivio()`` (R-27): si leggono, non si modificano.
Il piano è il JSON come lo ha scritto l'AI (``piano.contenuto``):

    {"strategia": "...",
     "uscite": [{"numero": 1, "tema": "...", "gruppo_id": 3,
                 "post": [{"canale": "facebook", "formato": "singola",
                           "foto": [12], "riempitivo": null,
                           "data_ora": "2030-01-07T10:00:00+01:00"}]}]}

Una cartolina non ha foto: la sua immagine nasce dopo il piano. Un riempitivo
`archivio` ha la sua foto, una di quelle già uscite sul canale (R-28).
"""

from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta
from typing import Any, TypedDict

from app.core.orologio import ROMA
from app.moduli.campagne import service as campagne

from .domain import FORMATI_POST, SCHEDE_CANALE

# R-28: i riempitivi che un piano può chiedere, in ordine di preferenza.
RIEMPITIVI_DEL_PIANO = ("archivio", "cartolina")

PIANO_MALFORMATO = "piano_malformato"
POST_PER_CANALE = "post_per_canale"
RIEMPITIVI = "riempitivi"
CAROSELLO_CON_RIEMPITIVI = "carosello_con_riempitivi"
FOTO_RIPETUTA = "foto_ripetuta"
FOTO_NON_DISPONIBILE = "foto_non_disponibile"
DATA_FUORI_PERIODO = "data_fuori_periodo"
DATA_NEL_PASSATO = "data_nel_passato"
FOTO_CON_STELLA = "foto_con_stella"
TROPPE_FOTO = "troppe_foto"
REGOLE = (
    PIANO_MALFORMATO,
    POST_PER_CANALE,
    RIEMPITIVI,
    CAROSELLO_CON_RIEMPITIVI,
    FOTO_RIPETUTA,
    FOTO_NON_DISPONIBILE,
    DATA_FUORI_PERIODO,
    DATA_NEL_PASSATO,
    FOTO_CON_STELLA,
    TROPPE_FOTO,
)


class LimitiCanale(TypedDict):
    """Limiti di un canale: un dizionario semplice, che si può dare all'AI."""

    post_chiesti: int
    foto_disponibili: list[int]
    # Foto d'archivio già uscite sul canale: solo per i riempitivi `archivio`.
    foto_riempitivo: list[int]
    riempitivi: int


class Violazione(TypedDict):
    """Una regola non rispettata dal piano; ``canale`` è vuoto se non ne riguarda uno."""

    regola: str
    canale: str | None
    messaggio: str


def _analisi(foto: Any) -> dict[str, Any]:
    return foto.analisi_ai if isinstance(foto.analisi_ai, dict) else {}


def _idonea(foto: Any) -> bool:
    return _analisi(foto).get("idonea") is True


def _caricate(gruppi: Iterable[Any]) -> list[Any]:
    """I gruppi di foto caricate: quelli `create_ai` la generazione li ignora (R-19)."""
    return [gruppo for gruppo in gruppi if gruppo.origine == "caricate"]


def _senza_doppioni(foto: Any) -> bool:
    """Idonea e senza `simile_a`: una foto non ancora analizzata non lo è."""
    return _idonea(foto) and not _analisi(foto).get("simile_a")


def foto_disponibili(gruppi: Iterable[Any]) -> list[int]:
    """Id delle foto caricate, idonee e senza `simile_a`, sommate sui gruppi (R-05).

    Sono le foto della campagna, le stesse su ogni canale: quelle d'archivio,
    che cambiano da un canale all'altro, le aggiunge ``limiti_per_canale()``.
    """
    return [
        foto.id
        for gruppo in _caricate(gruppi)
        for foto in gruppo.foto
        if _senza_doppioni(foto)
    ]


def foto_con_stella(gruppi: Iterable[Any]) -> list[int]:
    """Id delle foto con la stella e idonee: quelle che il piano deve usare (R-23)."""
    return [
        foto.id
        for gruppo in _caricate(gruppi)
        for foto in gruppo.foto
        if foto.da_usare and _idonea(foto)
    ]


def limiti_per_canale(
    canali: Iterable[str],
    post_a_settimana: int,
    inizio: date,
    fine: date,
    gruppi: Iterable[Any],
    archivio: Mapping[str, Iterable[Any]] | None = None,
) -> dict[str, LimitiCanale]:
    """Post chiesti, foto disponibili e riempitivi di ogni canale (R-05, R-28).

    ``canali`` sono quelli su cui la campagna esce ancora: un canale tolto non
    si passa. I post chiesti li calcola ``campagne.service.post_chiesti()``;
    i riempitivi sono i post chiesti che le foto non coprono.

    ``archivio`` ha, per canale, le foto di
    ``campagne.service.foto_di_archivio()``: quelle mai uscite lì si aggiungono
    alle foto disponibili, dopo quelle della campagna; quelle già uscite vanno
    in ``foto_riempitivo`` (R-27). Anche qui contano solo le foto idonee e
    senza `simile_a`.
    """
    chiesti = campagne.post_chiesti(post_a_settimana, inizio, fine)
    della_campagna = foto_disponibili(gruppi)
    limiti = {}
    for canale in canali:
        voci = [
            voce
            for voce in (archivio or {}).get(canale, ())
            if _senza_doppioni(voce.foto)
        ]
        disponibili = della_campagna + [v.foto.id for v in voci if v.mai_uscita]
        limiti[canale] = LimitiCanale(
            post_chiesti=chiesti,
            foto_disponibili=disponibili,
            foto_riempitivo=[v.foto.id for v in voci if not v.mai_uscita],
            riempitivi=max(0, chiesti - len(disponibili)),
        )
    return limiti


def piano_debole(limiti: Mapping[str, LimitiCanale], gruppi: Iterable[Any]) -> bool:
    """Piano debole (R-20).

    Su un canale le foto disponibili sono meno della metà dei post chiesti,
    oppure un gruppo di foto caricate non ha nessuna foto idonea.
    """
    poche_foto = any(
        2 * len(limite["foto_disponibili"]) < limite["post_chiesti"]
        for limite in limiti.values()
    )
    gruppo_senza_idonee = any(
        not any(_idonea(foto) for foto in gruppo.foto) for gruppo in _caricate(gruppi)
    )
    return poche_foto or gruppo_senza_idonee


def _intero(valore: Any) -> bool:
    return isinstance(valore, int) and not isinstance(valore, bool)


def _testo(valore: Any) -> bool:
    return isinstance(valore, str) and bool(valore.strip())


def _data_ora(valore: Any) -> datetime | None:
    """Data e ora ISO 8601 con il fuso, oppure `None` se non lo è."""
    if not isinstance(valore, str):
        return None
    try:
        letta = datetime.fromisoformat(valore)
    except ValueError:
        return None
    return letta if letta.utcoffset() is not None else None


def _difetti_del_post(post: Any, dove: str) -> list[str]:
    if not isinstance(post, dict):
        return [f"{dove}: un post non è un oggetto."]
    difetti = []
    if not _testo(post.get("canale")):
        return [f"{dove}: un post non ha il canale."]
    dove = f"{dove}, post {post['canale']}"

    formato = post.get("formato")
    if formato not in FORMATI_POST:
        difetti.append(f"{dove}: il formato deve essere uno tra {list(FORMATI_POST)}.")
    riempitivo = post.get("riempitivo")
    if riempitivo is not None and riempitivo not in RIEMPITIVI_DEL_PIANO:
        difetti.append(
            f"{dove}: il riempitivo deve essere vuoto o uno tra "
            f"{list(RIEMPITIVI_DEL_PIANO)}."
        )
    foto = post.get("foto")
    if not isinstance(foto, list) or not all(_intero(una) for una in foto):
        difetti.append(f"{dove}: le foto devono essere un elenco di id.")
    if _data_ora(post.get("data_ora")) is None:
        difetti.append(
            f"{dove}: data e ora devono essere in formato ISO 8601, con il fuso."
        )
    if difetti:
        return difetti

    if riempitivo == "archivio":
        if len(foto) != 1 or formato != "singola":
            difetti.append(
                f"{dove}: un riempitivo d'archivio è un post singolo, con una sola foto."
            )
    elif riempitivo is not None:
        if foto or formato != "singola":
            difetti.append(
                f"{dove}: una cartolina è un post singolo, senza foto del piano."
            )
    elif formato == "singola" and len(foto) != 1:
        difetti.append(f"{dove}: un post singolo ha una sola foto.")
    elif formato == "carosello" and len(foto) < 2:
        difetti.append(f"{dove}: un carosello ha almeno due foto.")
    return difetti


def _difetti(contenuto: Any, gruppi_ammessi: set[int]) -> list[str]:
    """Ciò che impedisce di leggere il piano o di salvarlo com'è."""
    if not isinstance(contenuto, dict):
        return ["Il piano non è un oggetto."]
    difetti = []
    if not _testo(contenuto.get("strategia")):
        difetti.append("Il piano non ha la strategia.")
    uscite = contenuto.get("uscite")
    if not isinstance(uscite, list):
        return difetti + ["Il piano non ha l'elenco delle uscite."]

    numeri: set[int] = set()
    for posizione, uscita in enumerate(uscite, start=1):
        if not isinstance(uscita, dict):
            difetti.append(f"L'uscita in posizione {posizione} non è un oggetto.")
            continue
        numero = uscita.get("numero")
        if not _intero(numero):
            difetti.append(f"L'uscita in posizione {posizione} non ha il numero.")
            continue
        dove = f"Uscita {numero}"
        if numero in numeri:
            difetti.append(f"{dove}: il numero è ripetuto.")
        numeri.add(numero)
        if not _testo(uscita.get("tema")):
            difetti.append(f"{dove}: manca il tema.")
        gruppo_id = uscita.get("gruppo_id")
        if gruppo_id is not None and not (
            _intero(gruppo_id) and gruppo_id in gruppi_ammessi
        ):
            difetti.append(
                f"{dove}: il gruppo non è tra i gruppi di foto caricate della "
                f"campagna né tra quelli dell'archivio."
            )
        post = uscita.get("post")
        if not isinstance(post, list) or not post:
            difetti.append(f"{dove}: non ha post.")
            continue
        canali: set[str] = set()
        for uno in post:
            difetti += _difetti_del_post(uno, dove)
            canale = uno.get("canale") if isinstance(uno, dict) else None
            if _testo(canale):
                if canale in canali:
                    difetti.append(f"{dove}: più di un post su {canale}.")
                canali.add(canale)
    return difetti


def _violazione(regola: str, canale: str | None, messaggio: str) -> Violazione:
    return Violazione(regola=regola, canale=canale, messaggio=messaggio)


def controlla_piano(
    contenuto: Any,
    *,
    limiti: Mapping[str, LimitiCanale],
    gruppi: Iterable[Any],
    inizio: date,
    fine: date,
    adesso: datetime,
    margine_minuti: int,
    archivio: Mapping[str, Iterable[Any]] | None = None,
) -> list[Violazione]:
    """Regole che il piano non rispetta; elenco vuoto se il piano è valido.

    Un piano malformato esce subito, con i soli difetti di forma: le altre
    regole si leggono solo su un piano che ha la forma attesa. L'elenco si può
    salvare in ``piano.esito_controllo`` e ridare all'AI per la riscrittura.

    Args:
        contenuto: il piano come lo ha scritto l'AI.
        limiti: i limiti di ``limiti_per_canale()`` per i canali della campagna.
        gruppi: i gruppi della campagna con le loro foto, già analizzate.
        inizio, fine: il periodo della campagna, estremi compresi (Europe/Rome).
        adesso: l'ora di riferimento, con il fuso.
        margine_minuti: anticipo minimo di un post su ``adesso`` (R-08).
        archivio: le foto d'archivio date a ``limiti_per_canale()``: un'uscita
            può avere il gruppo di una di queste.
    """
    gruppi = list(gruppi)
    gruppi_ammessi = {gruppo.id for gruppo in _caricate(gruppi)} | {
        voce.gruppo.id for voci in (archivio or {}).values() for voce in voci
    }
    difetti = _difetti(contenuto, gruppi_ammessi)
    if difetti:
        return [_violazione(PIANO_MALFORMATO, None, difetto) for difetto in difetti]

    # (numero dell'uscita, post), nell'ordine del piano
    post = [(u["numero"], p) for u in contenuto["uscite"] for p in u["post"]]
    canali = list(limiti) + sorted({p["canale"] for _, p in post} - set(limiti))
    del_canale = {c: [(n, p) for n, p in post if p["canale"] == c] for c in canali}
    violazioni: list[Violazione] = []

    for canale in canali:
        presenti = len(del_canale[canale])
        if canale not in limiti:
            messaggio = f"Il canale {canale} non è tra i canali della campagna."
            violazioni.append(_violazione(POST_PER_CANALE, canale, messaggio))
        elif presenti != limiti[canale]["post_chiesti"]:
            messaggio = (
                f"Su {canale} i post devono essere "
                f"{limiti[canale]['post_chiesti']}: sono {presenti}."
            )
            violazioni.append(_violazione(POST_PER_CANALE, canale, messaggio))

    con_riempitivi = set()
    for canale, limite in limiti.items():
        presenti = sum(1 for _, p in del_canale[canale] if p["riempitivo"] is not None)
        if presenti or limite["riempitivi"]:
            con_riempitivi.add(canale)
        if presenti != limite["riempitivi"]:
            messaggio = (
                f"Su {canale} i riempitivi devono essere {limite['riempitivi']}, "
                f"cioè i post chiesti che le foto disponibili non coprono: "
                f"sono {presenti}."
            )
            violazioni.append(_violazione(RIEMPITIVI, canale, messaggio))
            continue
        # R-28: una cartolina solo quando le foto d'archivio sono finite.
        d_archivio = sum(
            1 for _, p in del_canale[canale] if p["riempitivo"] == "archivio"
        )
        attesi = min(limite["riempitivi"], len(limite["foto_riempitivo"]))
        if d_archivio != attesi:
            messaggio = (
                f"Su {canale} i riempitivi `archivio` devono essere {attesi}, "
                f"perché le foto d'archivio vengono prima delle cartoline: "
                f"sono {d_archivio}."
            )
            violazioni.append(_violazione(RIEMPITIVI, canale, messaggio))

    for canale in limiti:
        if canale not in con_riempitivi:
            continue
        for numero, uno in del_canale[canale]:
            if uno["formato"] == "carosello":
                messaggio = (
                    f"Uscita {numero}: su {canale} ci sono riempitivi, "
                    f"quindi nessun carosello."
                )
                violazioni.append(
                    _violazione(CAROSELLO_CON_RIEMPITIVI, canale, messaggio)
                )

    for canale in limiti:
        usi = Counter(foto for _, p in del_canale[canale] for foto in p["foto"])
        for foto, volte in usi.items():
            if volte > 1:
                messaggio = f"Su {canale} la foto {foto} compare {volte} volte."
                violazioni.append(_violazione(FOTO_RIPETUTA, canale, messaggio))

    for canale, limite in limiti.items():
        disponibili = set(limite["foto_disponibili"])
        di_riempitivo = set(limite["foto_riempitivo"])
        # (foto, è di un riempitivo `archivio`), una volta sola
        usate = dict.fromkeys(
            (foto, p["riempitivo"] == "archivio")
            for _, p in del_canale[canale]
            for foto in p["foto"]
        )
        for foto, da_archivio in usate:
            if da_archivio and foto not in di_riempitivo:
                messaggio = (
                    f"Su {canale} la foto {foto} non è tra le foto d'archivio "
                    f"per i riempitivi."
                )
                violazioni.append(_violazione(FOTO_NON_DISPONIBILE, canale, messaggio))
            elif not da_archivio and foto not in disponibili:
                messaggio = f"Su {canale} la foto {foto} non è tra le foto disponibili."
                violazioni.append(_violazione(FOTO_NON_DISPONIBILE, canale, messaggio))

    limite_passato = adesso + timedelta(minutes=margine_minuti)
    fuori_periodo, nel_passato = [], []
    for numero, uno in post:
        quando = _data_ora(uno["data_ora"])
        dove = f"Uscita {numero}, post {uno['canale']}"
        if not inizio <= quando.astimezone(ROMA).date() <= fine:
            messaggio = f"{dove}: la data è fuori dal periodo della campagna."
            fuori_periodo.append(
                _violazione(DATA_FUORI_PERIODO, uno["canale"], messaggio)
            )
        if quando < limite_passato:
            messaggio = (
                f"{dove}: data e ora devono essere almeno {margine_minuti} "
                f"minuti dopo adesso."
            )
            nel_passato.append(_violazione(DATA_NEL_PASSATO, uno["canale"], messaggio))
    violazioni += fuori_periodo + nel_passato

    # R-23: con più stelle che post chiesti ne bastano quanti sono i post chiesti,
    # così un piano valido esiste sempre (una foto con la stella per post).
    stelle = foto_con_stella(gruppi)
    nel_piano = {foto for _, p in post for foto in p["foto"]}
    fuori = [foto for foto in stelle if foto not in nel_piano]
    chiesti = max((limite["post_chiesti"] for limite in limiti.values()), default=0)
    if len(stelle) <= chiesti:
        for foto in fuori:
            messaggio = f"La foto {foto} ha la stella e non è in nessun post."
            violazioni.append(_violazione(FOTO_CON_STELLA, None, messaggio))
    elif len(stelle) - len(fuori) < chiesti:
        messaggio = (
            f"Le foto con la stella sono {len(stelle)}, più dei post chiesti: "
            f"il piano ne deve usare almeno {chiesti}, ne usa "
            f"{len(stelle) - len(fuori)}."
        )
        violazioni.append(_violazione(FOTO_CON_STELLA, None, messaggio))

    for numero, uno in post:
        scheda = SCHEDE_CANALE.get(uno["canale"])
        if scheda is not None and len(uno["foto"]) > scheda["max_foto"]:
            messaggio = (
                f"Uscita {numero}, post {uno['canale']}: al massimo "
                f"{scheda['max_foto']} foto per post."
            )
            violazioni.append(_violazione(TROPPE_FOTO, uno["canale"], messaggio))

    return violazioni
