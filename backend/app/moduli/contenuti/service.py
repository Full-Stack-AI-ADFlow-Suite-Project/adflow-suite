"""Logica del modulo contenuti: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errori import DatiNonValidi
from app.core.transizioni import verifica_transizione
from app.moduli.campagne import service as campagne

from .domain import APPROVATO, ESITI_PUBBLICAZIONE, FALLITO, PUBBLICATO, TRANSIZIONI
from .models import Post, VersionePost


def post_della_campagna(
    db: Session,
    campagna_id: int,
) -> list[Post]:
    """Restituisce i post della campagna con versione corrente e storico.

    La versione corrente è l'ultima (plan §2). Usata da ``revisione``
    per mostrare all'operatore il contenuto da approvare e lo storico
    delle versioni precedenti.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna_id: chiave primaria della campagna.

    Returns:
        Lista di ``Post`` in ordine di data: ``post.versione_corrente`` è
        la versione corrente, ``post.versioni`` lo storico completo.
        Lista vuota se la campagna non ha post.
    """
    return list(
        db.scalars(
            select(Post)
            .where(Post.campagna_id == campagna_id)
            .options(selectinload(Post.versioni))
            .order_by(Post.data_ora, Post.id)
            .execution_options(populate_existing=True)
        )
    )


def ha_blocchi(
    db: Session,
    campagna_id: int,
) -> bool:
    """Indica se la campagna ha post con il segnale ``da_rivedere`` attivo.

    Usata da ``revisione`` prima di approvare: se restituisce ``True``
    l'operatore deve prima gestire i post segnalati dall'AI.
    ``da_rivedere`` è un campo bool del post, non uno stato (plan §2).
    L'«intervento in corso» di R-14 nasce con la rigenerazione (sprint 2b):
    quando arriva, si aggiunge qui.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna_id: chiave primaria della campagna da controllare.

    Returns:
        ``True`` se almeno un post ha ``da_rivedere = True``,
        ``False`` altrimenti.
    """
    return (
        db.scalar(
            select(Post.id)
            .where(Post.campagna_id == campagna_id, Post.da_rivedere.is_(True))
            .limit(1)
        )
        is not None
    )


def approva_post(
    db: Session,
    campagna_id: int,
) -> list[VersionePost]:
    """Porta tutti i post della campagna allo stato ``approvato``.

    L'approvazione è sempre in blocco sull'intera campagna: non esiste
    l'approvazione del singolo post (constitution §1.1). Restituisce le
    versioni approvate perché ``revisione`` scrive una riga di
    ``approvazione`` per ognuna (plan §6).

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna_id: chiave primaria della campagna da approvare.

    Returns:
        Lista delle versioni di post appena approvate.

    Raises:
        StatoNonValido: se uno dei post non è in stato ``da_approvare``.
    """
    post = post_della_campagna(db, campagna_id)
    for uno in post:
        verifica_transizione(TRANSIZIONI, uno.stato, APPROVATO)
    for uno in post:
        uno.stato = APPROVATO
    db.flush()
    return [uno.versione_corrente for uno in post if uno.versione_corrente]


def post_dovuti(
    db: Session,
    adesso: datetime,
) -> list[Post]:
    """Restituisce i post pronti per la pubblicazione al momento indicato.

    Un post è «dovuto» se: stato ``approvato``, ``data_ora`` raggiunta,
    campagna in stato ``attiva``. Usata da ``pubblicazione`` nel job
    ``tick_pubblicazione`` ogni minuto.

    Riceve ``adesso`` come argomento e non chiama ``datetime.now()``
    internamente: questo permette di iniettare un'ora fissa nei test
    (plan §7, ``core/orologio.py``).

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        adesso: istante di riferimento in UTC.

    Returns:
        Lista di post ``approvati`` con ``data_ora <= adesso`` e campagna
        ``attiva``. Lista vuota se non ce ne sono.
    """
    # Lo stato della campagna si legge dal service di campagne, che ne è proprietario.
    attive = [c.id for c in campagne.campagne_in_stato(db, ["attiva"])]
    if not attive:
        return []
    return list(
        db.scalars(
            select(Post)
            .where(
                Post.stato == APPROVATO,
                Post.data_ora <= adesso,
                Post.campagna_id.in_(attive),
            )
            .order_by(Post.data_ora, Post.id)
        )
    )


def segna_esito(
    db: Session,
    post: Post,
    esito: str,
) -> None:
    """Aggiorna lo stato del post dopo un tentativo di pubblicazione.

    Usata da ``pubblicazione`` dopo ogni chiamata all'adattatore social.
    Gli stati possibili come esito sono ``"pubblicato"`` o ``"fallito"``
    (plan §2). Lo stato del post appartiene a ``contenuti`` (constitution §2.4):
    per questo è ``contenuti`` a esporre questa funzione.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        post: il record ``Post`` da aggiornare (già caricato in sessione).
        esito: ``"pubblicato"`` se la pubblicazione è andata a buon fine,
               ``"fallito"`` dopo l'esaurimento dei tentativi.

    Raises:
        DatiNonValidi: se ``esito`` non è ``pubblicato`` né ``fallito``.
        StatoNonValido: se la transizione non è ammessa dal domain.
    """
    if esito not in ESITI_PUBBLICAZIONE:
        raise DatiNonValidi("Esito della pubblicazione non valido.")
    verifica_transizione(TRANSIZIONI, post.stato, esito)
    post.stato = esito
    db.flush()


def tutti_chiusi(
    db: Session,
    campagna_id: int,
) -> bool:
    """Indica se tutti i post della campagna sono pubblicati o falliti.

    È la condizione di spec §2.4 e CA-39. Usata da ``pubblicazione`` per
    sapere quando portare la campagna allo stato ``conclusa``.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna_id: chiave primaria della campagna da controllare.

    Returns:
        ``True`` se ogni post è ``pubblicato`` o ``fallito``, ``False`` se
        almeno uno è in un altro stato (es. ``approvato``, in attesa).
    """
    return (
        db.scalar(
            select(Post.id)
            .where(
                Post.campagna_id == campagna_id,
                Post.stato.not_in((PUBBLICATO, FALLITO)),
            )
            .limit(1)
        )
        is None
    )
