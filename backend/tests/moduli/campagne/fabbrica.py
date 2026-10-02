"""Fabbriche di base; stati e letture comuni arrivano con T1-04."""
from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy.orm import Session
from app.moduli.campagne.models import Campagna, Foto
from tests.moduli.artigiani.fabbrica import profilo


def campagna_in_bozza(
    db: Session, *, profilo_id: int | None = None, **campi
) -> Campagna:
    if profilo_id is None:
        profilo_id = profilo(db).id
    dati = dict(
        profilo_id=profilo_id,
        titolo="Campagna di prova",
        inizio=date(2030, 1, 1),
        fine=date(2030, 1, 31),
        stato="bozza",
    )
    dati.update(campi)
    record = Campagna(**dati)
    db.add(record)
    db.flush()
    return record


def _inviata(db: Session, stato: str, **campi) -> Campagna:
    dati = dict(
        stato=stato,
        canali=["instagram"],
        frequenza="f1_2",
        obiettivo="notorieta",
        profilo_snapshot={
            "nome": "Bottega di prova",
            "canali": ["instagram"],
            "frequenza": "f1_2",
            "obiettivo": "notorieta",
        },
        inviata_il=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    dati.update(campi)
    return campagna_in_bozza(db, **dati)


def campagna_inviata(db: Session, **campi) -> Campagna:
    return _inviata(db, "inviata", **campi)


def campagna_in_revisione(db: Session, **campi) -> Campagna:
    return _inviata(db, "in_revisione", **campi)


def campagna_attiva(db: Session, **campi) -> Campagna:
    return _inviata(db, "attiva", **campi)


def foto(db: Session, *, campagna: Campagna | None = None, **campi) -> Foto:
    campagna = campagna if campagna is not None else campagna_in_bozza(db)
    dati = dict(
        profilo_id=campagna.profilo_id,
        campagna_id=campagna.id,
        gruppo_id=uuid4(),
        file=f"{uuid4().hex}.jpg",
        mime="image/jpeg",
        larghezza=800,
        altezza=600,
    )
    dati.update(campi)
    record = Foto(**dati)
    db.add(record)
    db.flush()
    return record
