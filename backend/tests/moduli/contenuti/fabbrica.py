"""Post e versione iniziale con dati fittizi, senza commit."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.moduli.contenuti.models import Post, VersionePost
from tests.moduli.campagne.fabbrica import campagna_in_revisione, campagna_attiva, foto


def post_da_approvare(db: Session, *, campagna_id: int | None = None, **campi) -> Post:
    if campagna_id is None:
        campagna = campagna_in_revisione(db)
        immagine = foto(db, campagna=campagna)
        campagna_id = campagna.id
        foto_id = immagine.id
    else:
        foto_id = None
    dati = dict(
        campagna_id=campagna_id,
        canale="instagram",
        data_ora=datetime(2030, 1, 5, 12, tzinfo=timezone.utc),
        stato="da_approvare",
    )
    dati.update(campi)
    record = Post(**dati)
    db.add(record)
    db.flush()
    db.add(
        VersionePost(
            post_id=record.id,
            numero=1,
            testo="Testo di prova",
            hashtag=["artigianato"],
            foto_id=foto_id,
            tipo_intervento="generazione",
            provider_ai="finto",
            modello_ai="finto",
            versione_prompt="test-1",
        )
    )
    db.flush()
    return record


def post_approvato(db: Session, *, campagna_id: int | None = None, **campi) -> Post:
    if campagna_id is None:
        campagna_id = campagna_attiva(db).id
    dati = dict(stato="approvato")
    dati.update(campi)
    return post_da_approvare(db, campagna_id=campagna_id, **dati)
