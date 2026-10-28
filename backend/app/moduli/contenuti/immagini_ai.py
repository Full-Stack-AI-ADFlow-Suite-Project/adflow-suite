"""Immagini AI dei post di rimpiazzo (spec R-28, R-43, R-44; brief-ai T3-34).

Un'uscita senza foto ha un'immagine sola, la stessa su tutti i canali: la crea
il primo dei suoi post che si scrive, gli altri la trovano già fatta. Così una
nuova esecuzione non la ricrea (R-24).
"""

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.ai import AIAdapter, ErroreAI, prompt_immagine
from app.adapters.archivio import ottieni_archivio
from app.core.orologio import ROMA
from app.moduli.campagne import service as campagne

from . import service
from .domain import DICITURA_IMMAGINE_AI, IMMAGINE_AI
from .models import Post

ORIGINE = "creata_ai"
ESTENSIONI = {"image/png": "png", "image/jpeg": "jpg"}
# La regola di un blocco senza testo, nella versione del post che non ha l'immagine.
IMMAGINE_NON_CREATA = "immagine_non_creata"


@dataclass
class EsitoImmagine:
    """L'immagine del post, o il motivo per cui non c'è (``errore``)."""

    foto: Any | None = None
    errore: str | None = None


def con_dicitura(testo: str) -> str:
    """Il testo con «Immagine creata con AI» in fondo, una volta sola (R-43)."""
    if testo.rstrip().endswith(DICITURA_IMMAGINE_AI):
        return testo
    return f"{testo.rstrip()}\n\n{DICITURA_IMMAGINE_AI}"


def blocco_immagine_non_creata(errore: str) -> dict[str, str]:
    """La voce di ``errori_validazione`` di un post la cui immagine non è nata."""
    return {
        "livello": "blocco",
        "regola": IMMAGINE_NON_CREATA,
        "messaggio": f"Immagine non creata. {errore}",
    }


def _gia_deciso(db: Session, post: Post) -> EsitoImmagine | None:
    """Ciò che un altro post della stessa uscita ha già trovato: immagine o blocco."""
    altri = db.scalars(
        select(Post)
        .where(
            Post.uscita_id == post.uscita_id,
            Post.id != post.id,
            Post.riempitivo == IMMAGINE_AI,
        )
        .order_by(Post.id)
    )
    for altro in altri:
        versione = altro.versione_corrente
        if versione is None:
            continue
        foto = campagne.foto_per_id(db, [l.foto_id for l in versione.legami_foto])
        creata = next((una for una in foto if una.origine == ORIGINE), None)
        if creata is not None:
            return EsitoImmagine(foto=creata)
        for errore in versione.errori_validazione or []:
            if errore["regola"] == IMMAGINE_NON_CREATA:
                return EsitoImmagine(errore=errore["messaggio"])
    return None


def descrizione_immagine(campagna: Any, post: Post, tema: str) -> str:
    """Che cosa mostra l'immagine AI del post: il prompt con cui è stata chiesta.

    Va a chi scrive il testo, che non vede l'immagine ma deve richiamarla.
    """
    snapshot = campagna.profilo_snapshot
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    return prompt_immagine(snapshot, tema, post.data_ora.astimezone(ROMA).date())


def immagine_del_post(
    db: Session, campagna: Any, ai: AIAdapter, post: Post, tema: str
) -> EsitoImmagine:
    """L'immagine AI di un post `immagine_ai`: quella dell'uscita, o una nuova.

    Se il provider non accetta il prompt (`richiesta` o `rifiuto`) si prova una
    seconda volta con un prompt senza tono né stagione; se fallisce ancora il
    post resta senza foto e la generazione continua (R-35). Ogni altro errore
    dell'AI esce. La chiamata riuscita si registra subito in `chiamata_ai`
    (R-44). Senza commit.
    """
    esistente = _gia_deciso(db, post)
    if esistente is not None:
        return esistente
    snapshot = campagna.profilo_snapshot
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    giorno = post.data_ora.astimezone(ROMA).date()

    ultimo: ErroreAI | None = None
    for semplice in (False, True):
        try:
            immagine = ai.genera_immagine(
                prompt_immagine(snapshot, tema, giorno, semplice=semplice)
            )
        except ErroreAI as errore:
            if errore.tipo not in ("richiesta", "rifiuto"):
                raise
            ultimo = errore
            continue
        service.registra_chiamata_ai(db, campagna.id, ai.ultimo_uso, post_id=post.id)
        return EsitoImmagine(foto=_salva(db, campagna.id, immagine))
    return EsitoImmagine(errore=ultimo.messaggio if ultimo else "")


def _salva(db: Session, campagna_id: int, immagine: Any) -> Any:
    """Il file nell'archivio e la foto `creata_ai`, senza gruppo.

    Se la foto non si crea, il file appena salvato si elimina. Se la transazione
    di chi chiama viene annullata più tardi, il file resta senza foto: è un file
    orfano, innocuo.
    """
    with Image.open(BytesIO(immagine.contenuto)) as aperta:
        larghezza, altezza = aperta.size
    archivio = ottieni_archivio()
    file = archivio.salva(immagine.contenuto, ESTENSIONI[immagine.mime])
    try:
        return campagne.aggiungi_foto(
            db, campagna_id, ORIGINE, file, immagine.mime, larghezza, altezza
        )
    except Exception:
        archivio.elimina(file)
        raise
