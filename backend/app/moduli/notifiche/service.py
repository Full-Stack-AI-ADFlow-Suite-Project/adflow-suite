"""Logica del modulo notifiche: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.coda import INVIA_NOTIFICA, accoda
from app.core.errori import DatiNonValidi
from app.moduli.accesso import service as accesso

from . import domain

from .models import Notifica

# Namespace distinto dai lock a una chiave usati da altri moduli.
_LOCK_NOTIFICHE = 0x4E4F5449


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
    if tipo not in domain.TIPI:
        raise DatiNonValidi("Tipo di notifica non valido.")
    if adesso.tzinfo is None or adesso.utcoffset() is None:
        raise DatiNonValidi("L'istante della notifica deve avere un fuso orario.")
    if tipo in domain.TIPI_DI_UN_POST:
        if post_id is None:
            raise DatiNonValidi("Indicare il post della notifica.")
    else:
        post_id = None

    if domain.DESTINATARI[tipo] == domain.ARTIGIANO:
        if artigiano_id is None:
            raise DatiNonValidi("Indicare l'artigiano destinatario della notifica.")
        persona = accesso.utente(db, artigiano_id)
        if persona.ruolo != "artigiano":
            raise DatiNonValidi("Il destinatario deve essere un artigiano.")
        destinatari = [persona]
    else:
        destinatari = accesso.operatori(db)
    if not destinatari:
        return []

    # Il lock dura fino al termine della transazione del chiamante. Una seconda
    # creazione attende il commit/rollback e rilegge le notifiche già presenti.
    db.execute(
        text("SELECT pg_advisory_xact_lock(:modulo, :campagna)"),
        {"modulo": _LOCK_NOTIFICHE, "campagna": campagna_id},
    )
    gia_notificati = set(
        db.scalars(
            select(Notifica.utente_id).where(
                Notifica.campagna_id == campagna_id,
                Notifica.tipo == tipo,
                Notifica.post_id == post_id,
            )
        )
    )
    nuove = [
        Notifica(
            utente_id=persona.id,
            campagna_id=campagna_id,
            post_id=post_id,
            tipo=tipo,
            canale=domain.CANALE_EMAIL,
            stato_invio=domain.DA_INVIARE,
            creata_il=adesso.astimezone(timezone.utc),
        )
        for persona in destinatari
        if persona.id not in gia_notificati
    ]
    if not nuove:
        return []
    db.add_all(nuove)
    db.flush()
    # La coda ha una connessione propria: dopo tutti i flush, per ultima.
    for notifica in nuove:
        accoda(INVIA_NOTIFICA, notifica_id=notifica.id)
    return nuove
