"""Logo personale della bottega (T2a-12, R-40), senza commit nel modulo."""
from datetime import datetime
from io import BytesIO
import warnings

from PIL import Image, UnidentifiedImageError
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app.adapters.archivio import ottieni_archivio
from app.core.errori import DatiNonValidi, NonTrovato

from .models import ProfiloBottega

MAX_BYTE = 2 * 1024 * 1024
MIN_LATO = 300
FORMATO = {
    "JPEG": (".jpg", "image/jpeg"),
    "PNG": (".png", "image/png"),
    "WEBP": (".webp", "image/webp"),
}


def _profilo(db: Session, utente_id: int, *, blocca: bool = False) -> ProfiloBottega:
    query = select(ProfiloBottega).where(ProfiloBottega.utente_id == utente_id)
    if blocca:
        query = query.with_for_update().execution_options(populate_existing=True)
    record = db.scalar(query)
    if record is None:
        raise NonTrovato("Profilo della bottega non trovato.")
    return record


def _immagine(dati: bytes) -> tuple[str, str]:
    if not dati or len(dati) > MAX_BYTE:
        raise DatiNonValidi("Il logo deve essere un'immagine di al massimo 2 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(dati)) as immagine:
                if immagine.format not in FORMATO:
                    raise DatiNonValidi("Il logo deve essere JPG, PNG o WEBP.")
                formato = FORMATO[immagine.format]
                if min(immagine.size) < MIN_LATO:
                    raise DatiNonValidi(
                        "Il lato corto del logo deve essere di almeno 300 px."
                    )
                immagine.verify()
            with Image.open(BytesIO(dati)) as immagine:
                immagine.load()
        return formato
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise DatiNonValidi(
            "Il logo non è un'immagine valida: usare JPG, PNG o WEBP."
        ) from None


def salva(db: Session, utente_id: int, dati: bytes, ora: datetime) -> ProfiloBottega:
    record = _profilo(db, utente_id, blocca=True)
    estensione, _ = _immagine(dati)
    archivio = ottieni_archivio()
    nome = archivio.salva(dati, estensione)
    salvato = {"commit": False, "eliminato": False}

    def annulla(_db: Session) -> None:
        if not salvato["commit"] and not salvato["eliminato"]:
            archivio.elimina(nome)
            salvato["eliminato"] = True

    def conferma(_db: Session) -> None:
        salvato["commit"] = True

    event.listen(db, "after_rollback", annulla)
    event.listen(db, "after_commit", conferma)
    try:
        record.logo = nome
        record.aggiornato_il = ora
        db.flush()
    except Exception:
        annulla(db)
        raise
    return record


def leggi(db: Session, utente_id: int) -> tuple[bytes, str]:
    record = _profilo(db, utente_id)
    if not record.logo:
        raise NonTrovato("Logo della bottega non trovato.")
    try:
        dati = ottieni_archivio().leggi(record.logo)
        with Image.open(BytesIO(dati)) as immagine:
            mime = FORMATO[immagine.format][1]
    except (OSError, ValueError, KeyError, UnidentifiedImageError):
        raise NonTrovato("Logo della bottega non trovato.") from None
    return dati, mime


def elimina(db: Session, utente_id: int, ora: datetime) -> None:
    record = _profilo(db, utente_id, blocca=True)
    if not record.logo:
        raise NonTrovato("Logo della bottega non trovato.")
    record.logo = None
    record.aggiornato_il = ora
    db.flush()
