"""Logica del modulo notifiche: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime

from sqlalchemy.orm import Session

from .models import Notifica


def crea(
    db: Session,
    tipo: str,
    campagna_id: int,
    adesso: datetime,
    *,
    artigiano_id: int | None = None,
    post_id: int | None = None,
) -> list[Notifica]:
    """Scrive una notifica per ogni destinatario dell'evento e accoda l'email.

    Usata da ``contenuti``, ``revisione`` e ``pubblicazione`` (plan §6). Il
    tipo decide chi la riceve (``domain.DESTINATARI``): per i tipi degli
    operatori sono tutti gli operatori e gli admin attivi, letti con
    ``accesso.operatori()``; per quelli dell'artigiano è l'utente
    ``artigiano_id``, che chi chiama ha già a portata di mano. Ogni riga nasce
    ``da_inviare``, con canale ``email``, e per ognuna si accoda
    ``invia_notifica`` con ``accoda()``, per ultima, dopo ``flush``.

    Lo stesso evento non crea due volte la stessa notifica: se per un
    destinatario esiste già una notifica con lo stesso tipo, la stessa
    campagna e lo stesso ``post_id``, per lui non si scrive niente. Chi chiama
    può quindi richiamarla senza controllare (una nuova esecuzione del job di
    generazione, due tick di fila).

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        tipo: uno di ``domain.TIPI``.
        campagna_id: la campagna dell'evento.
        adesso: l'istante dell'evento, con il fuso: è ``creata_il``.
        artigiano_id: l'utente artigiano della campagna; obbligatorio per i
            tipi che lo riguardano, ignorato per gli altri.
        post_id: il post dell'evento; obbligatorio per i tipi di un post
            (``domain.TIPI_DI_UN_POST``), ignorato per gli altri.

    Returns:
        Le notifiche scritte adesso, una per destinatario; vuota se l'evento
        era già stato notificato a tutti.

    Raises:
        DatiNonValidi: tipo che non esiste, ``artigiano_id`` o ``post_id``
            mancanti dove servono.
    """
    raise NotImplementedError("T2b-11")
