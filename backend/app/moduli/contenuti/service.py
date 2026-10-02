"""Logica del modulo contenuti: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db


def post_della_campagna(
    db: Annotated[Session, Depends(get_db)],
    campagna_id: int,
) -> list[Any]:
    """Restituisce i post della campagna con versione corrente e storico.

    La versione corrente è l'ultima (plan §2). Usata da ``revisione``
    per mostrare all'operatore il contenuto da approvare e lo storico
    delle versioni precedenti.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna_id: chiave primaria della campagna.

    Returns:
        Lista di post, ognuno con la versione corrente e l'elenco
        completo delle versioni. Lista vuota se la campagna non ha post.

    Raises:
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04


def ha_blocchi(
    db: Annotated[Session, Depends(get_db)],
    campagna_id: int,
) -> bool:
    """Indica se la campagna ha post con il segnale ``da_rivedere`` attivo.

    Usata da ``revisione`` prima di approvare: se restituisce ``True``
    l'operatore deve prima gestire i post segnalati dall'AI.
    ``da_rivedere`` è un campo bool del post, non uno stato (plan §2).

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna_id: chiave primaria della campagna da controllare.

    Returns:
        ``True`` se almeno un post ha ``da_rivedere = True``,
        ``False`` altrimenti.

    Raises:
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04


def approva_post(
    db: Annotated[Session, Depends(get_db)],
    campagna_id: int,
) -> list[Any]:
    """Porta tutti i post della campagna allo stato ``approvato``.

    L'approvazione è sempre in blocco sull'intera campagna: non esiste
    l'approvazione del singolo post (constitution §1.1). Restituisce le
    versioni approvate perché ``pubblicazione`` ne ha bisogno per preparare
    i tentativi di pubblicazione.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna_id: chiave primaria della campagna da approvare.

    Returns:
        Lista delle versioni di post appena approvate.

    Raises:
        StatoNonValido: se uno dei post non è in stato ``da_approvare``.
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04


def post_dovuti(
    db: Annotated[Session, Depends(get_db)],
    adesso: datetime,
) -> list[Any]:
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

    Raises:
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04


def segna_esito(
    db: Annotated[Session, Depends(get_db)],
    post: Any,
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
        StatoNonValido: se la transizione non è ammessa dal domain.
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04


def tutti_chiusi(
    db: Annotated[Session, Depends(get_db)],
    campagna_id: int,
) -> bool:
    """Indica se tutti i post della campagna sono in uno stato finale.

    Gli stati finali di un post sono ``pubblicato``, ``fallito`` e
    ``scaduto`` (plan §2). Usata da ``pubblicazione`` per sapere quando
    portare la campagna allo stato ``conclusa``.

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        campagna_id: chiave primaria della campagna da controllare.

    Returns:
        ``True`` se tutti i post sono in stato finale, ``False`` se
        almeno uno è ancora ``approvato`` (in attesa di pubblicazione).

    Raises:
        NotImplementedError: stub — implementazione in T1-04.
    """
    raise NotImplementedError  # T1-04
