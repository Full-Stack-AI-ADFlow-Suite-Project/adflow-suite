"""Interventi dell'operatore sul testo di un post (spec §3, R-30)."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.errori import DatiNonValidi, StatoNonValido
from app.moduli.campagne import service as campagne

from .domain import DA_APPROVARE
from .models import VersionePost, VersionePostFoto
from .service import _azzera_spunta, _intervento_attivo, _post
from .validatore import BLOCCO, valida_testo


def _pulisci_hashtag(hashtag: list[str]) -> list[str]:
    """Gli hashtag come li salva l'AI: senza ``#``, senza spazi, senza voci vuote."""
    puliti = (uno.strip().lstrip("#").strip() for uno in hashtag)
    return [uno for uno in puliti if uno]


def modifica(
    db: Session,
    post_id: int,
    utente_id: int,
    testo: str,
    hashtag: list[str],
    adesso: datetime,
) -> VersionePost:
    """La modifica a mano come nuova versione ``modifica_operatore`` (R-30, CA-64).

    La versione ha lo stesso gruppo di foto della corrente e passa dal
    validatore (R-09): con un blocco, o con testo e hashtag uguali a quelli
    correnti, non si salva niente. Non conta cicli (R-03), azzera la spunta e,
    non avendo blocchi, toglie a un post ``da_rivedere`` il suo indicatore.
    Gli avvisi si salvano con la versione e non fermano nulla.
    """
    record = _post(db, post_id)
    campagna = campagne.campagna(db, record.campagna_id)
    if campagna.stato != "in_revisione":
        raise StatoNonValido("La campagna non è in revisione.")
    if record.stato != DA_APPROVARE:
        raise StatoNonValido("Il post non è da approvare.")
    if _intervento_attivo(record, adesso):
        raise StatoNonValido("Sul post c'è un intervento in corso.")
    corrente = record.versione_corrente
    if corrente is None:
        raise StatoNonValido("Il post non ha ancora un testo da modificare.")

    testo = testo.strip()
    hashtag = _pulisci_hashtag(hashtag)
    if testo == corrente.testo.strip() and hashtag == list(corrente.hashtag):
        raise DatiNonValidi("Il testo e gli hashtag sono uguali a quelli di prima.")
    snapshot = campagna.profilo_snapshot
    errori = [
        dict(errore)
        for errore in valida_testo(
            testo,
            hashtag,
            record.canale,
            snapshot if isinstance(snapshot, dict) else {},
        )
    ]
    blocchi = [errore["messaggio"] for errore in errori if errore["livello"] == BLOCCO]
    if blocchi:
        raise DatiNonValidi(" ".join(blocchi))

    nuova = VersionePost(
        post_id=record.id,
        numero=corrente.numero + 1,
        testo=testo,
        hashtag=hashtag,
        autore_id=utente_id,
        tipo_intervento="modifica_operatore",
        errori_validazione=errori,
    )
    db.add(nuova)
    db.flush()
    for legame in corrente.legami_foto:
        db.add(
            VersionePostFoto(
                versione_id=nuova.id,
                posizione=legame.posizione,
                foto_id=legame.foto_id,
            )
        )
    record.da_rivedere = False
    _azzera_spunta(record)
    db.flush()
    db.expire(record, ["versioni"])
    db.expire(nuova, ["legami_foto"])
    return nuova
