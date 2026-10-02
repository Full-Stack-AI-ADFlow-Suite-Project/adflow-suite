"""Logica del modulo pubblicazione: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db


def pubblica_dovuti(
    db: Annotated[Session, Depends(get_db)],
    adesso: datetime,
) -> None:
    """Pubblica sui social tutti i post approvati con data raggiunta.

    Chiamata da ``tick_pubblicazione`` in ``worker.py`` ogni minuto.
    Per ogni post dovuto (da ``contenuti.post_dovuti``):
    1. registra il tentativo di pubblicazione *prima* di chiamare il social
       (idempotenza — constitution §1.7);
    2. chiama l'adattatore social;
    3. registra l'esito e aggiorna lo stato del post;
    4. se tutti i post della campagna sono chiusi, porta la campagna a
       ``conclusa`` (tramite ``campagne.cambia_stato``).

    Riceve ``adesso`` come argomento e non chiama ``datetime.now()``
    internamente per permettere l'iniezione dell'ora nei test
    (plan §7, ``core/orologio.py``).

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        adesso: istante di riferimento in UTC.

    Raises:
        NotImplementedError: stub — implementazione in T1-43.
    """
    raise NotImplementedError  # T1-43
