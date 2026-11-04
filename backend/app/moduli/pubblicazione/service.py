"""Logica del modulo pubblicazione: l'unica parte che gli altri moduli possono importare."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.social import ottieni_social
from app.adapters.social.base import EsitoPubblicazione
from app.core.errori import DatiNonValidi, NonTrovato
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti
from app.moduli.notifiche import service as notifiche

from .models import Pubblicazione

# Dopo questo numero di tentativi un errore temporaneo diventa fallimento
# (spec §2.4: "errori temporanei ritentati", CA-38).
TENTATIVI_MAX = 3


def _notifica_post_fallito(db: Session, post, adesso: datetime) -> None:
    """Notifica `post_fallito` agli operatori, con titolo e canale nell'email."""
    campagna = campagne.campagna(db, post.campagna_id)
    notifiche.crea(
        db,
        "post_fallito",
        post.campagna_id,
        adesso,
        post_id=post.id,
        contenuto={
            "titolo": campagna.titolo,
            "canale": post.canale,
            "data_ora": post.data_ora.strftime("%d/%m/%Y %H:%M"),
        },
    )


ERRORE_ESITO_SCONOSCIUTO = (
    "Esito della pubblicazione sconosciuto: controlla la pagina prima di riprogrammare."
)


@dataclass(frozen=True)
class RichiestaSocial:
    """Tutto ciò che serve a chiamare il social, letto prima e senza più la sessione."""

    tentativo_id: int
    canale: str
    testo: str
    hashtag: list[str]
    byte_foto: list[bytes]
    url_foto: list[str]


def prepara_tentativi(db: Session, adesso: datetime) -> list[int]:
    """Prima fase: registra i tentativi dei post dovuti e ne torna gli id.

    Il chiamante fa commit subito dopo (constitution §2.6): da qui in poi il
    tentativo esiste nel database, qualunque cosa succeda al processo.
    Un tentativo ``in_corso`` con ``chiamata_il`` valorizzato e senza esito è
    di un processo morto a metà: la risposta del social non si conosce, quindi
    il post diventa ``fallito`` e **non si richiama il social** (RL-025,
    ADR-121: meglio un post non uscito che uscito due volte).
    """
    ids: list[int] = []
    for post in contenuti.post_dovuti(db, adesso):
        gia_ok = db.scalar(
            select(Pubblicazione.id)
            .where(Pubblicazione.post_id == post.id, Pubblicazione.stato == "ok")
            .limit(1)
        )
        if gia_ok is not None:
            continue

        versione = post.versione_corrente
        if versione is None:
            contenuti.segna_esito(db, post, "fallito")
            _notifica_post_fallito(db, post, adesso)
            continue

        sconosciuto = db.scalar(
            select(Pubblicazione)
            .where(
                Pubblicazione.post_id == post.id,
                Pubblicazione.stato == "in_corso",
                Pubblicazione.chiamata_il.is_not(None),
            )
            .with_for_update()
        )
        if sconosciuto is not None:
            _segna_errore(db, post, sconosciuto, ERRORE_ESITO_SCONOSCIUTO, adesso)
            continue

        ids.append(_registra_tentativo(db, post, versione.id, adesso).id)
    return ids


def avvia_chiamata(
    db: Session, tentativo_id: int, adesso: datetime
) -> RichiestaSocial | None:
    """Seconda fase, parte 1: scrive ``chiamata_il`` e prepara la richiesta.

    Il chiamante fa commit **prima** di chiamare il social: se il processo
    muore dopo, il tentativo porta ``chiamata_il`` e il tick successivo lo
    segnala invece di ripubblicare. Torna ``None`` se non c'è nulla da
    chiamare (controlli falliti, post non più dovuto, tentativo già preso da
    un altro tick: la riga è bloccata con ``FOR UPDATE``).
    """
    tentativo = db.scalar(
        select(Pubblicazione).where(Pubblicazione.id == tentativo_id).with_for_update()
    )
    if (
        tentativo is None
        or tentativo.stato != "in_corso"
        or tentativo.chiamata_il is not None
    ):
        return None
    post = contenuti.post_per_id(db, tentativo.post_id)
    versione = post.versione_corrente
    if post.stato != "approvato" or versione is None:
        return None

    problema = _verifica_pubblicabile(db, post, versione)
    if problema is not None:
        _segna_errore(db, post, tentativo, problema, adesso)
        return None

    try:
        # Congelato per l'MVP, ADR-114: non estendere. Nell'MVP un post ha
        # una foto sola; la pubblicazione con più foto (caroselli, A8) resta.
        # Byte della foto sistemata per il canale (R-42, T3-21) e suo
        # indirizzo pubblico firmato (T3-23): li usa l'adattatore Meta.
        byte_foto = [
            campagne.foto_sistemata(db, legame.foto_id, canale=post.canale)[0]
            for legame in versione.legami_foto
        ]
        url_foto = [
            campagne.url_foto_pubblica(db, legame.foto_id, canale=post.canale)
            for legame in versione.legami_foto
        ]
    except (NonTrovato, DatiNonValidi):
        _segna_errore(
            db,
            post,
            tentativo,
            "File della foto non trovato o non processabile.",
            adesso,
        )
        return None

    tentativo.chiamata_il = adesso
    db.flush()
    return RichiestaSocial(
        tentativo_id=tentativo.id,
        canale=post.canale,
        testo=versione.testo,
        hashtag=list(versione.hashtag),
        byte_foto=byte_foto,
        url_foto=url_foto,
    )


def chiama_social(richiesta: RichiestaSocial) -> EsitoPubblicazione:
    """Seconda fase, parte 2: la chiamata al social, senza sessione né transazione."""
    return ottieni_social().pubblica(
        richiesta.canale,
        richiesta.testo,
        richiesta.hashtag,
        richiesta.byte_foto,
        richiesta.url_foto,
    )


def registra_esito(
    db: Session, tentativo_id: int, esito: EsitoPubblicazione, adesso: datetime
) -> None:
    """Seconda fase, parte 3: registra la risposta del social e azzera ``chiamata_il``.

    Un esito ricevuto, anche temporaneo, chiude la «chiamata in volo»: l'errore
    temporaneo lascia il tentativo ``in_corso`` e il tick dopo riprova, fino a
    ``TENTATIVI_MAX``. Dopo un ``ok`` segna su ogni foto ``caricata`` il canale
    e l'istante (``campagne.segna_pubblicata``, R-27).
    """
    tentativo = db.scalar(
        select(Pubblicazione).where(Pubblicazione.id == tentativo_id).with_for_update()
    )
    post = contenuti.post_per_id(db, tentativo.post_id)
    versione = post.versione_corrente
    tentativo.chiamata_il = None
    if esito.ok:
        tentativo.stato = "ok"
        tentativo.id_esterno = esito.id_esterno
        foto_della_versione = {
            una.id: una
            for una in campagne.foto_per_id(
                db, [legame.foto_id for legame in versione.legami_foto]
            )
        }
        for legame in versione.legami_foto:
            immagine = foto_della_versione[legame.foto_id]
            if immagine.origine == "caricata":
                campagne.segna_pubblicata(db, immagine.id, post.canale, adesso)
        contenuti.segna_esito(db, post, "pubblicato")
    elif esito.tipo_errore == "temporaneo" and tentativo.n_tentativo < TENTATIVI_MAX:
        db.flush()  # resta in_corso: il prossimo tick riprova
    else:
        _segna_errore(
            db, post, tentativo, esito.errore or "Pubblicazione non riuscita.", adesso
        )


def chiudi_campagne(db: Session, adesso: datetime) -> None:
    """Ogni campagna ``attiva`` con tutti i post chiusi passa a ``conclusa`` (R-34)."""
    # La chiusura riguarda ogni campagna attiva, non solo quelle toccate in
    # questo tick: con un post fallito la conclusione arriva a periodo
    # finito, quando non c'è più niente di dovuto (R-34).
    for campagna in campagne.campagne_in_stato(db, ["attiva"]):
        if contenuti.tutti_chiusi(db, campagna.id, adesso):
            campagne.cambia_stato(db, campagna, "conclusa", ora=adesso)


def pubblica_dovuti(
    db: Session,
    adesso: datetime,
) -> None:
    """Pubblica sui social tutti i post approvati con data raggiunta, in una sessione sola.

    Compone le fasi senza commit, come i service (constitution §2.6): serve ai
    test e a chi ha già una transazione. Il worker (``tick_pubblicazione``)
    invece apre una transazione per fase, perché il tentativo e ``chiamata_il``
    siano confermati **prima** della chiamata al social (RL-025):
    1. ``prepara_tentativi`` · 2. per ogni tentativo ``avvia_chiamata``,
    ``chiama_social``, ``registra_esito`` · 3. ``chiudi_campagne``.

    Riceve ``adesso`` come argomento (plan §7, ``core/orologio.py``).
    """
    for tentativo_id in prepara_tentativi(db, adesso):
        richiesta = avvia_chiamata(db, tentativo_id, adesso)
        if richiesta is not None:
            registra_esito(db, tentativo_id, chiama_social(richiesta), adesso)
    chiudi_campagne(db, adesso)


def _registra_tentativo(
    db: Session, post, versione_id: int, adesso: datetime
) -> Pubblicazione:
    """Crea la riga del tentativo, o riusa quella ``in_corso``.

    Il tentativo esiste nel database *prima* della chiamata al social: se il
    processo muore a metà, il tick successivo riprende dalla riga ``in_corso``
    e non riparte da zero (idempotenza, constitution §1.7). Il numero del
    tentativo prosegue dopo un post riprogrammato (R-34).
    """
    in_corso = db.scalar(
        select(Pubblicazione)
        .where(Pubblicazione.post_id == post.id, Pubblicazione.stato == "in_corso")
        .with_for_update()
    )
    if in_corso is not None:
        in_corso.n_tentativo += 1
        in_corso.versione_id = versione_id
        in_corso.creata_il = adesso
        db.flush()
        return in_corso

    ultimo = (
        db.scalar(
            select(func.max(Pubblicazione.n_tentativo)).where(
                Pubblicazione.post_id == post.id
            )
        )
        or 0
    )
    tentativo = Pubblicazione(
        post_id=post.id,
        versione_id=versione_id,
        n_tentativo=ultimo + 1,
        stato="in_corso",
        creata_il=adesso,
    )
    db.add(tentativo)
    db.flush()
    return tentativo


def _verifica_pubblicabile(db: Session, post, versione) -> str | None:
    """Restituisce il motivo per cui non si può pubblicare, o ``None``.

    Controlli prima della chiamata al social: il post deve avere almeno una
    foto nella versione corrente e il suo canale deve avere l'account
    collegato. La sospensione della campagna per permesso scaduto (R-07) è
    fuori MVP: il post diventa ``fallito``.
    """
    if not versione.legami_foto:
        return "Il post non ha foto da pubblicare."
    profilo_id = campagne.campagna(db, post.campagna_id).profilo_id
    if post.canale not in artigiani.canali_collegati(db, profilo_id):
        return f"Il canale {post.canale} non è collegato."
    return None


def _segna_errore(
    db: Session, post, tentativo: Pubblicazione, messaggio: str, adesso: datetime
) -> None:
    """Chiude il tentativo in errore, porta il post a ``fallito`` e avvisa gli operatori (CA-55)."""
    tentativo.stato = "errore"
    tentativo.errore = messaggio
    contenuti.segna_esito(db, post, "fallito")
    _notifica_post_fallito(db, post, adesso)
