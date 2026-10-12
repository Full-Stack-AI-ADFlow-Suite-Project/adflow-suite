"""Nota interna, respingi e togli il canale (spec §2.3; R-15, R-18, R-32).

Gli endpoint di ``router.py`` chiamano queste funzioni: lo stato della
campagna cambia solo con ``campagne.cambia_stato()``, i post solo con
``contenuti`` e le decisioni si scrivono solo con
``campagne.registra_decisione()`` (plan §6, constitution §1). Ogni azione
registra la sua decisione; respingi manda anche la notifica
``campagna_respinta`` all'artigiano.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core import coda
from app.core.errori import DatiNonValidi, StatoNonValido
from app.moduli.accesso import service as accesso
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti
from app.moduli.notifiche import service as notifiche


def nota(db: Session, campagna_id: int, utente: accesso.Utente, testo: str) -> None:
    """Nota interna in ogni stato dopo l'invio: decisione ``nota`` (R-32).

    Nessun cambio di stato, nessuna email; la leggono solo gli operatori.

    Raises:
        NonTrovato: campagna che non esiste (404).
        StatoNonValido: la campagna è ancora ``bozza`` (409).
        DatiNonValidi: nota vuota (422).
    """
    record = campagne.campagna(db, campagna_id)
    if record.stato == "bozza":
        raise StatoNonValido("La nota interna vale dopo l'invio.")
    if not testo or not testo.strip():
        raise DatiNonValidi("La nota non può essere vuota.")
    campagne.registra_decisione(
        db,
        record,
        utente.id,
        "nota",
        motivo=None,
        nota=testo.strip(),
        foto_segnate=[],
    )


def respingi(
    db: Session,
    campagna_id: int,
    utente: accesso.Utente,
    motivo: str,
    testo: str,
    foto_segnate: list[int],
    adesso: datetime,
) -> None:
    """In revisione o piano da rivedere → ``respinta`` (R-15, R-18).

    I post ``da_approvare`` diventano ``scartato``, la decisione ``respinta``
    porta motivo, nota e foto da rifare, e la notifica ``campagna_respinta``
    va all'artigiano (CA-24, CA-25).

    Raises:
        NonTrovato: campagna che non esiste (404).
        StatoNonValido: la campagna non è ``in_revisione`` né
            ``piano_da_rivedere`` (409).
        DatiNonValidi: motivo o nota mancanti, oppure foto segnate che non
            sono della campagna (422).
    """
    record = campagne.campagna(db, campagna_id)
    if record.stato not in ("in_revisione", "piano_da_rivedere"):
        raise StatoNonValido(
            "Si respinge solo una campagna in revisione o con un piano da rivedere."
        )
    if motivo not in ("foto", "altro"):
        raise DatiNonValidi("Il motivo deve essere 'foto' o 'altro'.")
    if not testo or not testo.strip():
        raise DatiNonValidi("La nota è obbligatoria.")
    segnate = list(dict.fromkeys(foto_segnate))
    if segnate:
        della_campagna = {f.id for f in campagne.foto_della_campagna(db, campagna_id)}
        if not set(segnate) <= della_campagna:
            raise DatiNonValidi("Le foto segnate devono appartenere a questa campagna.")

    contenuti.scarta_post_della_campagna(db, campagna_id)
    campagne.registra_decisione(
        db,
        record,
        utente.id,
        "respinta",
        motivo=motivo,
        nota=testo.strip(),
        foto_segnate=segnate,
    )
    campagne.cambia_stato(db, record, "respinta", ora=adesso)
    profilo = artigiani.profilo(db, record.profilo_id)
    if profilo is not None:
        notifiche.crea(
            db,
            "campagna_respinta",
            campagna_id,
            adesso,
            artigiano_id=profilo.utente_id,
        )


def togli_canale(
    db: Session,
    campagna_id: int,
    utente: accesso.Utente,
    canale: str,
    testo: str,
    adesso: datetime,
) -> campagne.Campagna:
    """Toglie un canale: i suoi post scartati, decisione ``canale_tolto``.

    Ammesso in ``generazione_fallita``, ``piano_da_rivedere`` e
    ``in_revisione``; da ``generazione_fallita`` la campagna riparte con la
    generazione sui canali rimasti (plan §3). Togliere l'ultimo canale non è
    possibile (409, CA-53): il controllo sta in ``campagne.togli_canale()``.

    Raises:
        NonTrovato: campagna che non esiste (404).
        StatoNonValido: stato non ammesso o ultimo canale rimasto (409).
        DatiNonValidi: nota vuota o canale che non è della campagna (422).
    """
    record = campagne.campagna(db, campagna_id)
    if record.stato not in (
        "generazione_fallita",
        "piano_da_rivedere",
        "in_revisione",
    ):
        raise StatoNonValido(
            "Si può togliere un canale solo con la generazione fallita, "
            "un piano da rivedere o in revisione."
        )
    if not testo or not testo.strip():
        raise DatiNonValidi("La nota è obbligatoria.")
    era_fallita = record.stato == "generazione_fallita"
    campagne.togli_canale(db, record, canale)
    contenuti.scarta_post_del_canale(db, campagna_id, canale)
    campagne.registra_decisione(
        db,
        record,
        utente.id,
        "canale_tolto",
        motivo=None,
        nota=testo.strip(),
        foto_segnate=[],
        canale=canale,
    )
    if era_fallita:
        campagne.cambia_stato(db, record, "inviata", ora=adesso)
        coda.accoda(coda.GENERA_CAMPAGNA, campagna_id=record.id)
    return record
