"""Campagne, gruppi e foto di prova, senza commit.

Le campagne dall'invio in poi sono complete: canali, frequenza e obiettivo
copiati dal profilo, fotografia del profilo e un gruppo con 4 foto.
"""
from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.moduli.artigiani.models import ProfiloBottega
from app.moduli.campagne.models import Campagna, Foto, GruppoFoto
from tests.moduli.artigiani.fabbrica import profilo

# L'analisi di una foto che il piano può usare (plan §2, `foto.analisi_ai`).
ANALISI_IDONEA = {
    "idonea": True,
    "simile_a": None,
    "tipo": "pezzo_finito",
    "punteggio": 0.8,
    "motivo": None,
    "soggetto": "Oggetto di prova",
}


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


def campagna_conclusa(db: Session, **campi) -> Campagna:
    """Campagna chiusa nell'autunno 2029: le sue 4 foto sono idonee e mai pubblicate.

    È una delle due fonti dell'archivio della bottega (spec R-27). Dove è
    uscita una foto lo decide il test, con ``foto.pubblicata_su``.
    """
    dati = dict(
        inizio=date(2029, 10, 1),
        fine=date(2029, 10, 31),
        inviata_il=datetime(2029, 9, 15, tzinfo=timezone.utc),
        chiusa_il=datetime(2029, 11, 1, tzinfo=timezone.utc),
    )
    dati.update(campi)
    record = _inviata(db, "conclusa", **dati)
    for immagine in db.scalars(select(Foto).where(Foto.campagna_id == record.id)):
        immagine.analisi_ai = dict(ANALISI_IDONEA)
    db.flush()
    return record


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


def gruppo_di_archivio(
    db: Session, *, profilo_id: int | None = None, n_foto: int = 2, **campi
) -> GruppoFoto:
    """Gruppo dell'archivio della bottega: senza campagna, caricato dal profilo.

    Ha ``n_foto`` foto idonee e mai pubblicate (spec R-27). Una foto ancora da
    analizzare si aggiunge con ``foto(db, gruppo=...)``.
    """
    if profilo_id is None:
        profilo_id = profilo(db).id
    dati = dict(
        profilo_id=profilo_id,
        campagna_id=None,
        origine="caricate",
        descrizione="Gruppo d'archivio di prova",
    )
    dati.update(campi)
    record = GruppoFoto(**dati)
    db.add(record)
    db.flush()
    for _ in range(n_foto):
        foto(db, gruppo=record, analisi_ai=dict(ANALISI_IDONEA))
    return record


def campagna_con_piano_da_rivedere(db: Session, **campi) -> Campagna:
    """Campagna inviata completa, ferma per un piano debole."""
    from tests.moduli.contenuti.fabbrica import piano

    record = _inviata(db, "piano_da_rivedere", **campi)
    piano(db, record, debole=True)
    return record
