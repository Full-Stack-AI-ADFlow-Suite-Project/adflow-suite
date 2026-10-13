"""Corpo di ``revisione.scadenze()``: il tick la chiama ogni minuto (plan §4).

Tre cose, tutte idempotenti (R-06, R-35, CA-30, CA-68):

- i post ``da_approvare`` con la data passata diventano ``scaduto``;
- una campagna con un piano diventa ``scaduta`` — con i post rimasti — quando
  i ``da_approvare`` sono meno della metà dei post chiesti sui canali non
  tolti; senza piano scade alle 00:00 (Europe/Rome) del giorno di inizio. In
  entrambi i casi l'artigiano riceve la notifica ``campagna_scaduta``;
- una campagna ferma da 30 minuti in ``inviata`` o ``in_generazione`` va in
  ``generazione_fallita`` con ``contenuti.ferma_generazione()``: è il caso del
  worker spento, non di una generazione che avanza — «ferma» si misura
  sull'ultimo progresso visibile (invio, piano, versioni, errori).
"""

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti
from app.moduli.notifiche import service as notifiche

ROMA = ZoneInfo("Europe/Rome")
FERMA_MINUTI = 30
# Oltre la fine dei tempi: scadi_post() con questo istante scade anche i post
# con la data nel futuro, come vuole la campagna che diventa scaduta (CA-30).
OLTRE_LA_FINE = datetime.max.replace(tzinfo=timezone.utc)
# Stati dai quali la campagna può passare a scaduta (plan §2).
SCADIBILI = (
    "inviata",
    "in_generazione",
    "piano_da_rivedere",
    "generazione_fallita",
    "in_revisione",
)
FERME = ("inviata", "in_generazione")


def scadenze(db: Session, adesso: datetime) -> None:
    """Applica le scadenze morbide e ferma le campagne bloccate (R-06, R-35)."""
    for record in campagne.campagne_in_stato(db, list(SCADIBILI)):
        _scadenza_morbida(db, record, adesso)
        if record.stato in FERME:
            _ferma_se_ferma(db, record, adesso)


def _scadenza_morbida(db: Session, record, adesso: datetime) -> None:
    """Scade i post passati e, se la campagna è sotto la soglia, la campagna."""
    contenuti.scadi_post(db, record.id, adesso)
    piano = contenuti.piano_corrente(db, record.id)
    scade = (
        _giorno_di_inizio_passato(record, adesso)
        if piano is None
        else _pochi_post_rimasti(db, record)
    )
    if not scade:
        return
    # I post da_approvare rimasti scadono con la campagna (CA-30).
    contenuti.scadi_post(db, record.id, OLTRE_LA_FINE)
    _notifica_artigiano(db, record, adesso)
    campagne.cambia_stato(db, record, "scaduta", ora=adesso)


def _giorno_di_inizio_passato(record, adesso: datetime) -> bool:
    """Vero se sono passate le 00:00 di Roma del giorno di inizio (R-06)."""
    mezzanotte = datetime.combine(record.inizio, time.min, tzinfo=ROMA)
    return adesso >= mezzanotte


def _pochi_post_rimasti(db: Session, record) -> bool:
    """I ``da_approvare`` sono meno della metà dei post chiesti (R-06)."""
    tolti = set(record.canali_tolti or [])
    canali = [c for c in record.canali or [] if c not in tolti]
    post_sett = artigiani.post_a_settimana(record.frequenza)
    chiesti = campagne.post_chiesti(post_sett, record.inizio, record.fine)
    chiesti *= len(canali)
    rimasti = sum(
        1
        for post in contenuti.post_della_campagna(db, record.id)
        if post.stato == "da_approvare"
    )
    return rimasti * 2 < chiesti


def _notifica_artigiano(db: Session, record, adesso: datetime) -> None:
    profilo = artigiani.profilo(db, record.profilo_id)
    if profilo is None:
        return
    notifiche.crea(
        db,
        "campagna_scaduta",
        record.id,
        adesso,
        artigiano_id=profilo.utente_id,
        contenuto={"titolo": record.titolo},
    )


def _ferma_se_ferma(db: Session, record, adesso: datetime) -> None:
    """Nessun progresso da 30 minuti → ``generazione_fallita`` (R-35, CA-68)."""
    if adesso - _ultima_attivita(db, record) >= timedelta(minutes=FERMA_MINUTI):
        contenuti.ferma_generazione(db, record.id, adesso)


def _ultima_attivita(db: Session, record) -> datetime:
    """L'ultimo progresso visibile: invio, piano, versioni o errori."""
    momenti = [record.inviata_il] if record.inviata_il is not None else []
    piano = contenuti.piano_corrente(db, record.id)
    if piano is not None:
        momenti.append(piano.creata_il)
    errore = contenuti.ultimo_errore(db, record.id)
    if errore is not None:
        momenti.append(errore.creata_il)
    for post in contenuti.post_della_campagna(db, record.id):
        momenti.extend(versione.creata_il for versione in post.versioni)
    # Nessuna traccia di progresso: la campagna è ferma da sempre.
    return max(momenti, default=datetime.min.replace(tzinfo=timezone.utc))
