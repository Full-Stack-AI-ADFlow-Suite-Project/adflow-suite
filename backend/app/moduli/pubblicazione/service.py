"""Logica del modulo pubblicazione: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.archivio import ottieni_archivio
from app.adapters.social import ottieni_social
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti

from .models import Pubblicazione

# Dopo questo numero di tentativi un errore temporaneo diventa fallimento
# (spec §2.4: "errori temporanei ritentati", CA-38).
TENTATIVI_MAX = 3


def pubblica_dovuti(
    db: Session,
    adesso: datetime,
) -> None:
    """Pubblica sui social tutti i post approvati con data raggiunta.

    Chiamata da ``tick_pubblicazione`` in ``worker.py`` ogni minuto.
    Per ogni post dovuto (da ``contenuti.post_dovuti``):
    1. registra il tentativo di pubblicazione *prima* di chiamare il social
       (idempotenza — constitution §1.7);
    2. chiama l'adattatore social con testo, hashtag e tutte le foto della
       versione corrente, nell'ordine di ``versione_post_foto.posizione``
       (per una cartolina la sua immagine);
    3. registra l'esito: errore ``temporaneo`` lascia il tentativo
       ``in_corso`` per il tick successivo, fino a ``TENTATIVI_MAX``;
    4. alla fine, ogni campagna ``attiva`` con tutti i post chiusi passa a
       ``conclusa`` (R-34, tramite ``campagne.cambia_stato``).

    Riceve ``adesso`` come argomento e non chiama ``datetime.now()``
    internamente per permettere l'iniezione dell'ora nei test
    (plan §7, ``core/orologio.py``).

    Args:
        db: sessione del database (aperta e chiusa dal chiamante).
        adesso: istante di riferimento in UTC.
    """
    for post in contenuti.post_dovuti(db, adesso):
        _pubblica_post(db, post, adesso)

    # La chiusura riguarda ogni campagna attiva, non solo quelle toccate in
    # questo tick: con un post fallito la conclusione arriva a periodo
    # finito, quando non c'è più niente di dovuto (R-34).
    for campagna in campagne.campagne_in_stato(db, ["attiva"]):
        if contenuti.tutti_chiusi(db, campagna.id, adesso):
            campagne.cambia_stato(db, campagna, "conclusa", ora=adesso)


def _pubblica_post(db: Session, post, adesso: datetime) -> None:
    """Un tentativo di pubblicazione per il singolo post."""
    gia_ok = db.scalar(
        select(Pubblicazione.id)
        .where(Pubblicazione.post_id == post.id, Pubblicazione.stato == "ok")
        .limit(1)
    )
    if gia_ok is not None:
        return

    versione = post.versione_corrente
    if versione is None:
        contenuti.segna_esito(db, post, "fallito")
        return

    tentativo = _registra_tentativo(db, post, versione.id, adesso)

    problema = _verifica_pubblicabile(db, post, versione)
    if problema is not None:
        _segna_errore(db, post, tentativo, problema)
        return

    archivio = ottieni_archivio()
    nomi = {
        foto.id: foto.file
        for foto in campagne.foto_della_campagna(db, post.campagna_id)
    }
    try:
        byte_foto = [
            archivio.leggi(nomi[legame.foto_id]) for legame in versione.legami_foto
        ]
    except (KeyError, FileNotFoundError):
        _segna_errore(db, post, tentativo, "File della foto non trovato nell'archivio.")
        return

    esito = ottieni_social().pubblica(versione.testo, list(versione.hashtag), byte_foto)
    if esito.ok:
        tentativo.stato = "ok"
        tentativo.id_esterno = esito.id_esterno
        contenuti.segna_esito(db, post, "pubblicato")
    elif esito.tipo_errore == "temporaneo" and tentativo.n_tentativo < TENTATIVI_MAX:
        pass  # resta in_corso: il prossimo tick riprova
    else:
        _segna_errore(
            db, post, tentativo, esito.errore or "Pubblicazione non riuscita."
        )


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
        select(Pubblicazione).where(
            Pubblicazione.post_id == post.id, Pubblicazione.stato == "in_corso"
        )
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
    collegato (la sospensione della campagna per permesso scaduto, R-07,
    arriva nello sprint 3).
    """
    if not versione.legami_foto:
        return "Il post non ha foto da pubblicare."
    profilo_id = campagne.campagna(db, post.campagna_id).profilo_id
    if post.canale not in artigiani.canali_collegati(db, profilo_id):
        return f"Il canale {post.canale} non è collegato."
    return None


def _segna_errore(db: Session, post, tentativo: Pubblicazione, messaggio: str) -> None:
    """Chiude il tentativo in errore e porta il post a ``fallito``."""
    tentativo.stato = "errore"
    tentativo.errore = messaggio
    contenuti.segna_esito(db, post, "fallito")
