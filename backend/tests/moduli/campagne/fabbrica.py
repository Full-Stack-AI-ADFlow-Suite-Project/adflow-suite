"""Campagne, gruppi e foto di prova, senza commit.

Le campagne dall'invio in poi sono complete: canali, frequenza e obiettivo
copiati dal profilo, fotografia del profilo e un gruppo con 4 foto.
"""
from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy.orm import Session
from app.moduli.artigiani.models import ProfiloBottega
from app.moduli.campagne.models import Campagna, Foto, GruppoFoto
from tests.moduli.artigiani.fabbrica import profilo


def campagna_in_bozza(
    db: Session, *, profilo_id: int | None = None, **campi
) -> Campagna:
    if profilo_id is None:
        profilo_id = profilo(db).id
    bottega = db.get(ProfiloBottega, profilo_id)
    dati = dict(
        profilo_id=profilo_id,
        titolo="Campagna di prova",
        inizio=date(2030, 1, 1),
        fine=date(2030, 1, 31),
        stato="bozza",
        canali=list(bottega.canali),
    )
    dati.update(campi)
    record = Campagna(**dati)
    db.add(record)
    db.flush()
    return record


def _fotografia(bottega: ProfiloBottega) -> dict:
    return {
        colonna.name: getattr(bottega, colonna.name)
        for colonna in ProfiloBottega.__table__.columns
        if colonna.name not in ("id", "aggiornato_il")
    }


def _inviata(
    db: Session, stato: str, *, profilo_id: int | None = None, **campi
) -> Campagna:
    bottega = profilo(db) if profilo_id is None else db.get(ProfiloBottega, profilo_id)
    dati = dict(
        stato=stato,
        canali=list(bottega.canali),
        frequenza=bottega.frequenza,
        obiettivo=bottega.obiettivo,
        profilo_snapshot=_fotografia(bottega),
        inviata_il=datetime(2029, 12, 1, tzinfo=timezone.utc),
    )
    dati.update(campi)
    record = campagna_in_bozza(db, profilo_id=bottega.id, **dati)
    mazzo = gruppo(db, record)
    for _ in range(4):
        foto(db, gruppo=mazzo)
    return record


def campagna_inviata(db: Session, **campi) -> Campagna:
    return _inviata(db, "inviata", **campi)


def campagna_in_revisione(db: Session, **campi) -> Campagna:
    return _inviata(db, "in_revisione", **campi)


def campagna_attiva(db: Session, **campi) -> Campagna:
    return _inviata(db, "attiva", **campi)


def gruppo(
    db: Session,
    campagna: Campagna | None = None,
    *,
    origine: str = "caricate",
    **campi,
) -> GruppoFoto:
    if campagna is None:
        campagna = campagna_in_bozza(db)
    dati = dict(
        profilo_id=campagna.profilo_id,
        campagna_id=campagna.id,
        origine=origine,
        descrizione="Gruppo di prova",
        n_immagini=3 if origine == "create_ai" else None,
    )
    dati.update(campi)
    record = GruppoFoto(**dati)
    db.add(record)
    db.flush()
    return record


_nuovo_gruppo = gruppo


def foto(
    db: Session,
    *,
    gruppo: GruppoFoto | None = None,
    campagna: Campagna | None = None,
    **campi,
) -> Foto:
    if gruppo is None:
        gruppo = _nuovo_gruppo(db, campagna or campagna_in_bozza(db))
    dati = dict(
        profilo_id=gruppo.profilo_id,
        campagna_id=gruppo.campagna_id,
        gruppo_id=gruppo.id,
        file=f"{uuid4().hex}.jpg",
        mime="image/jpeg",
        larghezza=1080,
        altezza=1350,
    )
    dati.update(campi)
    record = Foto(**dati)
    db.add(record)
    db.flush()
    return record


def campagna_con_piano_da_rivedere(db: Session, **campi) -> Campagna:
    """Campagna inviata completa, ferma per un piano debole."""
    from tests.moduli.contenuti.fabbrica import piano

    record = _inviata(db, "piano_da_rivedere", **campi)
    piano(db, record, debole=True)
    return record
