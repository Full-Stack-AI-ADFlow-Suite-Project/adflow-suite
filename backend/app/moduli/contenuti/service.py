"""Logica del modulo contenuti: l'unica parte che gli altri moduli possono importare."""

from collections.abc import Iterable
from datetime import datetime, timedelta

from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session, selectinload

from app.core.config import leggi_impostazioni
from app.core.errori import DatiNonValidi, NonTrovato, StatoNonValido
from app.core.orologio import ROMA
from app.core.transizioni import verifica_transizione
from app.moduli.campagne import service as campagne

from .domain import (
    APPROVATO,
    ANNULLATO,
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


def _post_in_stato(
    db: Session, campagna_id: int, stato: str, *condizioni
) -> list[Post]:
    """I post della campagna in quello stato, in ordine di data."""
    return list(
        db.scalars(
            select(Post)
            .where(Post.campagna_id == campagna_id, Post.stato == stato, *condizioni)
            .order_by(Post.data_ora, Post.id)
        )
    )


def _porta_a(db: Session, post: list[Post], nuovo: str) -> list[Post]:
    """Cambia lo stato di tutti i post o di nessuno, con ``verifica_transizione()``."""
    for uno in post:
        verifica_transizione(TRANSIZIONI, uno.stato, nuovo)
    for uno in post:
        uno.stato = nuovo
    db.flush()
    return post


def _post(db: Session, post_id: int) -> Post:
    record = db.get(Post, post_id)
    if record is None:
        raise NonTrovato("Post non trovato.")
    return record


def _azzera_spunta(post: Post) -> None:
    """La spunta «va bene» vale per una versione e una data: se cambiano, cade (R-30)."""
    post.controllato_da = None
    post.controllato_il = None


def _intervento_attivo(post: Post, adesso: datetime) -> bool:
    """Un intervento partito da più di 10 minuti vale come fallito (R-31)."""
    return (
        post.intervento_in_corso is not None
        and post.intervento_dal is not None
        and post.intervento_dal > adesso - timedelta(minutes=10)
    )


def scarta_post_della_campagna(db: Session, campagna_id: int) -> list[Post]:
    """Porta a ``scartato`` tutti i post ``da_approvare`` della campagna.

    Usata da ``revisione`` quando si respinge (plan §6, spec R-18). Ogni
    cambio di stato passa da ``verifica_transizione()``. I post che non sono
    ``da_approvare`` restano come sono; l'ordine dei passaggi di campagna è di
    chi chiama.

    Returns:
        I post scartati adesso, in ordine di data; vuota se non ce n'erano.
    """
    return _porta_a(db, _post_in_stato(db, campagna_id, DA_APPROVARE), SCARTATO)


def scarta_post_del_canale(db: Session, campagna_id: int, canale: str) -> list[Post]:
    """Porta a ``scartato`` i post ``da_approvare`` di un canale della campagna.

    Usata da ``revisione`` quando si toglie un canale (plan §6, spec R-18,
    CA-53). Come ``scarta_post_della_campagna()``, ma solo per quel canale.

    Returns:
        I post scartati adesso, in ordine di data; vuota se non ce n'erano.
    """
    da_scartare = _post_in_stato(db, campagna_id, DA_APPROVARE, Post.canale == canale)
    return _porta_a(db, da_scartare, SCARTATO)


def scadi_post(db: Session, campagna_id: int, adesso: datetime) -> list[Post]:
    """Porta a ``scaduto`` i post ``da_approvare`` con la data passata (R-06).

    Usata da ``revisione.scadenze()`` a ogni tick (plan §6). Non decide se
    scade la campagna: questo lo guarda ``revisione``, sui post rimasti. Due
    chiamate di seguito con lo stesso ``adesso``: la seconda non cambia nulla.

    Returns:
        I post scaduti adesso, in ordine di data; vuota se non ce n'erano.
    """
    passati = _post_in_stato(db, campagna_id, DA_APPROVARE, Post.data_ora < adesso)
    return _porta_a(db, passati, SCADUTO)


def annulla_post(
    db: Session, campagna_id: int, post_ids: Iterable[int] | None = None
) -> list[Post]:
    """Porta ad ``annullato`` i post ``approvato`` della campagna (R-33).

    Usata da ``revisione`` per annullare la campagna (tutti i post approvati)
    e per riattivarla (solo gli arretrati che l'operatore non vuole pubblicare
    adesso). Con ``post_ids`` solo quei post, se sono ``approvato``; senza,
    tutti quelli approvati. Un post ``annullato`` è chiuso e non si pubblica.

    Returns:
        I post annullati adesso, in ordine di data; vuota se non ce n'erano.
    """
    condizioni = [] if post_ids is None else [Post.id.in_(list(post_ids))]
    approvati = _post_in_stato(db, campagna_id, APPROVATO, *condizioni)
    return _porta_a(db, approvati, ANNULLATO)


def riprogramma_post(
    db: Session, post_id: int, data_ora: datetime, adesso: datetime
) -> Post:
    """Rimette in coda un post ``fallito`` con una nuova data (R-34, CA-67).

    Usata da ``revisione`` per ``POST /post/{id}/riprogramma``: l'unico
    intervento sul singolo post che la campagna attiva o sospesa ammette
    (R-16). Il post torna ``approvato``; il contenuto non cambia. La
    decisione ``riprogrammato`` la registra chi chiama.

    Raises:
        NonTrovato: se non esiste nessun post con quell'id.
        StatoNonValido: il post non è ``fallito`` (409).
        DatiNonValidi: ``data_ora`` fuori dal periodo della campagna o a meno
            di 15 minuti da ``adesso`` (422).
    """
    record = _post(db, post_id)
    if record.stato != FALLITO:
        raise StatoNonValido("Si riprogramma solo un post fallito.")
    campagna = campagne.campagna(db, record.campagna_id)
    if campagna.stato not in ("attiva", "sospesa"):
        raise StatoNonValido("La campagna non è attiva né sospesa.")
    if data_ora.tzinfo is None:
        raise DatiNonValidi("La nuova data deve avere il fuso orario.")
    margine = leggi_impostazioni().margine_slot_minuti
    if data_ora < adesso + timedelta(minutes=margine):
        raise DatiNonValidi(
            f"La nuova data deve essere almeno {margine} minuti dopo adesso."
        )
    if not campagna.inizio <= data_ora.astimezone(ROMA).date() <= campagna.fine:
        raise DatiNonValidi("La nuova data deve cadere nel periodo della campagna.")
    verifica_transizione(TRANSIZIONI, record.stato, APPROVATO)
    record.data_ora = data_ora
    record.stato = APPROVATO
    _azzera_spunta(record)
    db.flush()
    return record


def segna_controllato(
    db: Session, post_id: int, utente_id: int, valore: bool, adesso: datetime
) -> Post:
    """Mette o toglie la spunta «va bene» di un post (R-30, CA-65).

    Usata da ``revisione`` (plan §6). Con ``valore`` vero salva ``utente_id`` in
    ``controllato_da`` e ``adesso`` in ``controllato_il``; con falso li svuota.
    La spunta si azzera da sola a ogni nuova versione e a ogni cambio di data.

    Raises:
        NonTrovato: se non esiste nessun post con quell'id.
        StatoNonValido: la campagna non è ``in_revisione``, il post non è
            ``da_approvare``, ha un intervento in corso o, per mettere la
            spunta, è ``da_rivedere`` (409).
    """
    record = _post(db, post_id)
    if campagne.campagna(db, record.campagna_id).stato != "in_revisione":
        raise StatoNonValido("La campagna non è in revisione.")
    if record.stato != DA_APPROVARE:
        raise StatoNonValido("Il post non è da approvare.")
    if _intervento_attivo(record, adesso):
        raise StatoNonValido("Sul post c'è un intervento in corso.")
    if valore and record.da_rivedere:
        raise StatoNonValido("Un post da rivedere non si può spuntare.")
    if valore:
        record.controllato_da = utente_id
        record.controllato_il = adesso
    else:
        _azzera_spunta(record)
    db.flush()
    return record


def modifica_post(
    db: Session,
    post_id: int,
    utente_id: int,
    testo: str,
    hashtag: list[str],
    adesso: datetime,
) -> VersionePost:
    """Salva la modifica a mano dell'operatore come nuova versione (R-30, CA-64).

    Usata da ``revisione`` (plan §6). Nasce una versione
    ``modifica_operatore`` con ``utente_id`` come autore, le stesse foto della
    precedente, passata dal validatore (R-09). Non conta cicli (R-03) e
    azzera la spunta. Un post ``da_rivedere`` si sblocca se la nuova versione
    non ha blocchi.

    Raises:
        NonTrovato: se non esiste nessun post con quell'id.
        StatoNonValido: campagna non ``in_revisione``, post non ``da_approvare``
            o con un intervento in corso (409).
        DatiNonValidi: la versione avrebbe un blocco o è uguale a quella
            corrente (422); nessuna versione si salva.
    """
    raise NotImplementedError("T2b-32")


def puo_rigenerare(db: Session, post_id: int, adesso: datetime) -> bool:
    """Vero se per il post si può chiedere una rigenerazione del testo (R-03, R-31).

    Usata da ``revisione`` prima di accendere l'intervento (plan §6). Serve che
    la campagna sia ``in_revisione``, il post ``da_approvare``, senza un
    intervento in corso partito da meno di 10 minuti e con meno di 3
    rigenerazioni del testo.

    Raises:
        NonTrovato: se non esiste nessun post con quell'id.
    """
    raise NotImplementedError("T2b-33")


def accendi_intervento(db: Session, post_id: int, tipo: str, adesso: datetime) -> Post:
    """Segna sul post che un intervento dell'AI è in corso (R-31).

    Usata da ``revisione`` prima di accodare ``rigenera_post`` (plan §6).
    Salva ``tipo`` (uno di ``TIPI_INTERVENTO_IN_CORSO``) in
    ``intervento_in_corso`` e ``adesso`` in ``intervento_dal``. Lo spegne il
    job quando nasce la versione o alla terza esecuzione fallita.

    Raises:
        NonTrovato: se non esiste nessun post con quell'id.
        StatoNonValido: ``puo_rigenerare()`` sarebbe falso (409).
        DatiNonValidi: ``tipo`` che non esiste (422).
    """
    raise NotImplementedError("T2b-33")


def ferma_generazione(db: Session, campagna_id: int, adesso: datetime) -> None:
    """Ferma una campagna rimasta bloccata in ``inviata`` o ``in_generazione`` (R-35).

    Usata da ``revisione.scadenze()`` per le campagne ferme da 30 minuti
    (plan §6, CA-68). Salva un ``ErroreGenerazione`` di tipo ``temporaneo`` con
    un messaggio per l'operatore, poi porta la campagna a
    ``generazione_fallita`` con ``campagne.cambia_stato()``. L'errore sta qui
    perché ``errore_generazione`` è di ``contenuti``.

    Raises:
        NonTrovato: se non esiste nessuna campagna con quell'id.
        StatoNonValido: la campagna non è ``inviata`` né ``in_generazione`` (409).
    """
    from .generazione import prossima_tappa  # generazione importa questo modulo

    record = campagne.campagna(db, campagna_id)
    if record.stato not in ("inviata", "in_generazione"):
        raise StatoNonValido("La campagna non è ferma in generazione.")
    db.add(
        ErroreGenerazione(
            campagna_id=record.id,
            tipo="temporaneo",
            messaggio="La generazione non ha fatto progressi per 30 minuti.",
            tappa=prossima_tappa(db, record, adesso) or "avvio",
            creata_il=adesso,
        )
    )
    campagne.cambia_stato(db, record, "generazione_fallita")
