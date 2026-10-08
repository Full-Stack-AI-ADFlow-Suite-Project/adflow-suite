"""Piani, uscite e post di prova con versione e foto, senza commit."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.moduli.campagne import service as campagne
from app.moduli.contenuti.models import (
    Piano,
    Post,
    Uscita,
    VersionePost,
    VersionePostFoto,
)
from tests.moduli.campagne.fabbrica import (
    campagna_in_revisione,
    campagna_attiva,
    foto,
)


def piano(db: Session, campagna=None, *, numero: int | None = None, **campi) -> Piano:
    if campagna is None:
        campagna = campagna_in_revisione(db)
    if numero is None:
        numero = (
            db.scalar(
                select(func.max(Piano.numero)).where(Piano.campagna_id == campagna.id)
            )
            or 0
        ) + 1
    dati = dict(
        campagna_id=campagna.id,
        numero=numero,
        strategia="Strategia di prova",
        contenuto={"uscite": []},
    )
    dati.update(campi)
    record = Piano(**dati)
    db.add(record)
    db.flush()
    return record


def uscita(
    db: Session, campagna=None, gruppo=None, *, numero: int | None = None, **campi
) -> Uscita:
    if campagna is None:
        campagna = campagna_in_revisione(db)
    if numero is None:
        numero = (
            db.scalar(
                select(func.max(Uscita.numero)).where(Uscita.campagna_id == campagna.id)
            )
            or 0
        ) + 1
    dati = dict(
        campagna_id=campagna.id,
        gruppo_id=gruppo.id if gruppo is not None else None,
        numero=numero,
        tema="Tema di prova",
    )
    dati.update(campi)
    record = Uscita(**dati)
    db.add(record)
    db.flush()
    return record


def post_da_approvare(db: Session, *, campagna_id: int | None = None, **campi) -> Post:
    if campagna_id is None:
        campagna_id = campagna_in_revisione(db).id
    campagna = campagne.campagna(db, campagna_id)
    # Usa la foto della campagna meno usata; se non ce ne sono ne crea una.
    disponibili = campagne.foto_della_campagna(db, campagna_id)
    if disponibili:
        immagine = min(disponibili, key=lambda f: (f.n_utilizzi, f.id))
    else:
        immagine = foto(db, campagna=campagna)
    immagine.n_utilizzi += 1
    gruppi = campagne.gruppi_della_campagna(db, campagna_id)
    mazzo = next((g for g in gruppi if g.id == immagine.gruppo_id), None)
    uscita_della_campagna = uscita(db, campagna, mazzo)
    dati = dict(
        campagna_id=campagna_id,
        uscita_id=uscita_della_campagna.id,
        canale="instagram",
        data_ora=datetime(2030, 1, 5, 12, tzinfo=timezone.utc),
        stato="da_approvare",
    )
    dati.update(campi)
    record = Post(**dati)
    db.add(record)
    db.flush()
    versione = VersionePost(
        post_id=record.id,
        numero=1,
        testo="Testo di prova",
        hashtag=["artigianato"],
        tipo_intervento="generazione",
        provider_ai="finto",
        modello_ai="finto",
        versione_prompt="test-1",
    )
    db.add(versione)
    db.flush()
    db.add(VersionePostFoto(versione_id=versione.id, posizione=1, foto_id=immagine.id))
    db.flush()
    return record


def post_approvato(db: Session, *, campagna_id: int | None = None, **campi) -> Post:
    if campagna_id is None:
        campagna_id = campagna_attiva(db).id
    dati = dict(stato="approvato")
    dati.update(campi)
    return post_da_approvare(db, campagna_id=campagna_id, **dati)
