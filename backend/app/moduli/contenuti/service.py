"""Logica del modulo contenuti: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime, timedelta

from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session, selectinload

from app.core.errori import DatiNonValidi, StatoNonValido
from app.core.orologio import ROMA
from app.core.transizioni import verifica_transizione
from app.moduli.campagne import service as campagne

from .domain import (
    APPROVATO,
    DA_APPROVARE,
    SCADUTO,
    SCARTATO,
    ESITI_PUBBLICAZIONE,
    FALLITO,
    TRANSIZIONI,
    STATI_CHIUSI,
)
from .models import Post, VersionePost, Piano, Uscita, ErroreGenerazione


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
        ``versione.legami_foto`` contiene i legami ordinati per posizione,
        con ``foto_id`` (non gli oggetti foto del modulo campagne).
        Lista vuota se la campagna non ha post.
    """
    return list(
        db.scalars(
            select(Post)
            .where(Post.campagna_id == campagna_id)
            .options(selectinload(Post.versioni).selectinload(VersionePost.legami_foto))
            .order_by(Post.data_ora, Post.id)
            .execution_options(populate_existing=True)
        )
    )


def ha_blocchi(db: Session, campagna_id: int, adesso: datetime) -> bool:
    """Post da approvare con blocchi o intervento avviato da meno di 10 minuti.

    I vecchi interventi non bloccano; non si modifica il loro storico (R-31).
    """
    return (
        db.scalar(
            select(Post.id)
            .where(
                Post.campagna_id == campagna_id,
                Post.stato == DA_APPROVARE,
                or_(
                    Post.da_rivedere.is_(True),
                    and_(
                        Post.intervento_in_corso.is_not(None),
                        Post.intervento_dal > adesso - timedelta(minutes=10),
                    ),
                ),
            )
            .limit(1)
        )
        is not None
    )


def approva_post(db: Session, campagna_id: int, adesso: datetime) -> list[VersionePost]:
    """Approva i post da approvare non passati, scade i passati (R-14).

    Mantiene scartati e scaduti. Tutti i controlli precedono le modifiche:
    senza post approvabili o con blocchi solleva StatoNonValido senza mutazioni.
    Restituisce le versioni approvate, per le righe di approvazione.
    """
    post = post_della_campagna(db, campagna_id)
    approvabili = [p for p in post if p.stato == DA_APPROVARE and p.data_ora >= adesso]
    if not approvabili:
        raise StatoNonValido("Non ci sono post da approvare.")
    if ha_blocchi(db, campagna_id, adesso):
        raise StatoNonValido("Ci sono post da rivedere o interventi in corso.")
    for uno in post:
        if uno.stato not in (SCARTATO, SCADUTO):
            if uno.stato != DA_APPROVARE:
                raise StatoNonValido(
                    "La campagna contiene post già usciti dalla revisione."
                )
            destinazione = APPROVATO if uno.data_ora >= adesso else SCADUTO
            verifica_transizione(TRANSIZIONI, uno.stato, destinazione)
    for uno in post:
        if uno.stato == DA_APPROVARE:
            uno.stato = APPROVATO if uno.data_ora >= adesso else SCADUTO
    db.flush()
    return [p.versione_corrente for p in approvabili if p.versione_corrente is not None]


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


def tutti_chiusi(db: Session, campagna_id: int, adesso: datetime) -> bool:
    """Tutti i post chiusi; con falliti attende la fine del periodo (R-34).

    La fine è inclusiva, nel fuso Europe/Rome. Nessun commit o cambio di stato.
    """
    stati = list(db.scalars(select(Post.stato).where(Post.campagna_id == campagna_id)))
    if any(stato not in STATI_CHIUSI for stato in stati):
        return False
    if FALLITO in stati:
        return adesso.astimezone(ROMA).date() > campagne.campagna(db, campagna_id).fine
    return True


def piano_corrente(db: Session, campagna_id: int) -> Piano | None:
    """Ultimo piano per numero, senza alterare lo storico."""
    return db.scalar(
        select(Piano)
        .where(Piano.campagna_id == campagna_id)
        .order_by(Piano.numero.desc())
        .limit(1)
    )


def uscite_della_campagna(db: Session, campagna_id: int) -> list[Uscita]:
    """Uscite in ordine di numero, anche prima della generazione dei testi."""
    return list(
        db.scalars(
            select(Uscita)
            .where(Uscita.campagna_id == campagna_id)
            .order_by(Uscita.numero)
        )
    )


def ultimo_errore(db: Session, campagna_id: int) -> ErroreGenerazione | None:
    """Ultimo errore per istante e id, per un ordine stabile a parità di ora."""
    return db.scalar(
        select(ErroreGenerazione)
        .where(ErroreGenerazione.campagna_id == campagna_id)
        .order_by(ErroreGenerazione.creata_il.desc(), ErroreGenerazione.id.desc())
        .limit(1)
    )
