"""Logica del modulo notifiche: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime, timezone
from io import BytesIO

from PIL import Image, ImageOps
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.adapters.archivio import ottieni_archivio
from app.adapters.email import Allegato, Email, ottieni_email
from app.core.coda import INVIA_NOTIFICA, accoda
from app.core.errori import DatiNonValidi
from app.moduli.accesso import service as accesso

from . import domain, testi

from .models import Notifica

# Namespace distinto dai lock a una chiave usati da altri moduli.
_LOCK_NOTIFICHE = 0x4E4F5449
_DIMENSIONI_MINIATURA = (320, 320)


def _miniatura(contenuto: bytes) -> bytes:
    """Riduce una foto segnata a una miniatura JPEG adatta all'email."""
    with Image.open(BytesIO(contenuto)) as immagine:
        immagine = ImageOps.exif_transpose(immagine)
        immagine.thumbnail(_DIMENSIONI_MINIATURA, Image.Resampling.LANCZOS)
        if immagine.mode != "RGB":
            immagine = immagine.convert("RGB")
        buffer = BytesIO()
        immagine.save(buffer, format="JPEG", optimize=True)
        return buffer.getvalue()


def crea(
    db: Session,
    tipo: str,
    campagna_id: int,
    adesso: datetime,
    *,
    artigiano_id: int | None = None,
    post_id: int | None = None,
    contenuto: dict | None = None,
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
        contenuto: i dati dell'evento per il testo dell'email (chiavi in
            ``testi.py``: titolo sempre, motivo/nota/foto per la respinta);
            deve essere serializzabile in JSON perché viaggia negli argomenti
            del job ``invia_notifica``.

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
        argomenti = {"notifica_id": notifica.id}
        if contenuto is not None:
            argomenti["contenuto"] = contenuto
        accoda(INVIA_NOTIFICA, **argomenti)
    return nuove


def invia(
    db: Session, notifica_id: int, contenuto: dict | None, adesso: datetime
) -> None:
    """Compone e spedisce l'email di una notifica ``da_inviare``.

    Il job ``invia_notifica`` la chiama (plan §4): il testo viene da
    ``testi.py`` con il ``contenuto`` passato da chi ha creato la notifica; le
    miniature segnate vengono lette dall'adattatore archivio. Una notifica già
    ``inviata`` o ``fallita`` non riparte: due esecuzioni del job non inviano
    due email.

    Raises:
        ErroreInvio: il trasporto email non è riuscito: il job riprova.
    """
    notifica = db.get(Notifica, notifica_id)
    if notifica is None or notifica.stato_invio != domain.DA_INVIARE:
        return
    persona = accesso.utente(db, notifica.utente_id)
    contenuto = contenuto or {}
    oggetto, corpo = testi.componi(notifica.tipo, contenuto, persona.nome)
    archivio = ottieni_archivio()
    allegati = [
        Allegato(
            nome=f"miniatura-{indice}.jpg",
            contenuto=_miniatura(archivio.leggi(foto["nome"])),
            mime="image/jpeg",
        )
        for indice, foto in enumerate(contenuto.get("foto") or [], start=1)
    ]
    ottieni_email().invia(
        Email(
            destinatario=persona.email,
            oggetto=oggetto,
            corpo=corpo,
            allegati=allegati,
        )
    )
    notifica.stato_invio = domain.INVIATA
    notifica.inviata_il = adesso


def segna_fallita(db: Session, notifica_id: int) -> None:
    """Esauriti i tentativi: la notifica resta ``fallita`` (plan §4)."""
    notifica = db.get(Notifica, notifica_id)
    if notifica is not None and notifica.stato_invio == domain.DA_INVIARE:
        notifica.stato_invio = domain.FALLITA
