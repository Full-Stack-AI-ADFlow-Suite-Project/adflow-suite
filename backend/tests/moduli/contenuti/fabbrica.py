"""Post di prova con la versione iniziale e la sua foto, senza commit."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.moduli.campagne import service as campagne
from app.moduli.contenuti.models import Post, VersionePost
from tests.moduli.campagne.fabbrica import campagna_in_revisione, campagna_attiva, foto


def post_da_approvare(db: Session, *, campagna_id: int | None = None, **campi) -> Post:
    if campagna_id is None:
        campagna_id = campagna_in_revisione(db).id
    # Usa la foto della campagna meno usata; se non ce ne sono ne crea una.
    disponibili = campagne.foto_della_campagna(db, campagna_id)
    if disponibili:
        immagine = min(disponibili, key=lambda f: (f.n_utilizzi, f.id))
    else:
        immagine = foto(db, campagna=campagne.campagna(db, campagna_id))
    immagine.n_utilizzi += 1
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
            foto_id=immagine.id,
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
