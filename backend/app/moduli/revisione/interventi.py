"""Interventi dell'operatore sul singolo post (spec §3, plan §3).

Gli endpoint di ``router.py`` chiamano queste funzioni: stati e versioni del
post e intervento in corso sono di ``contenuti`` (plan §6), la decisione è di
``campagne`` e il job ``rigenera_post`` si accoda per nome. Regole: R-03, R-16
(solo in ``in_revisione``; in attiva o sospesa solo la riprogrammazione),
R-30, R-31, R-34, R-36.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.coda import RIGENERA_POST, accoda
from app.core.errori import DatiNonValidi
from app.core.orologio import ROMA
from app.moduli.accesso import service as accesso
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti

from .models import Approvazione

FORMATO_DATA = "%d/%m/%Y %H:%M"

# La modalità che arriva dall'API e il tipo che il post salva (R-31).
MODALITA_RIGENERAZIONE = {
    "totale": "rigenera_totale",
    "da_proposta": "rigenera_da_proposta",
}


def _approva_se_approvata(db: Session, versione, utente: accesso.Utente) -> None:
    """Dopo l'approvazione la versione dell'operatore nasce approvata (spec R-16)."""
    campagna = campagne.campagna(db, versione.post.campagna_id)
    if campagna.stato in ("attiva", "sospesa"):
        db.add(
            Approvazione(
                versione_id=versione.id,
                utente_id=utente.id,
                ruolo=utente.ruolo,
                esito="approvato",
            )
        )
        db.flush()


def modifica(
    db: Session,
    post_id: int,
    utente: accesso.Utente,
    testo: str,
    hashtag: list[str],
    adesso: datetime,
):
    """Modifica a mano: nasce una versione ``modifica_operatore`` (R-30, CA-64, CA-84).

    I controlli (``modifica`` ammessa sul post, testo diverso e senza blocchi)
    sono in ``contenuti.modifica_post()``: 404, 409 e 422 escono da lì. Dopo
    l'approvazione la versione nuova ha subito la riga ``approvazione`` di chi
    la scrive.
    """
    nuova = contenuti.modifica_post(db, post_id, utente.id, testo, hashtag, adesso)
    _approva_se_approvata(db, nuova, utente)
    return nuova


def sposta(
    db: Session, post_id: int, utente_id: int, data_ora: datetime, adesso: datetime
):
    """Sposta il post a un'altra data e ora, con la decisione ``riprogrammato`` (R-36, CA-72).

    I controlli (``sposta`` ammesso, data nel periodo e dopo il margine, data
    diversa) sono in ``contenuti.sposta_post()``. La nota dice da quando a quando.
    """
    post, prima = contenuti.sposta_post(db, post_id, data_ora, adesso)
    nota = (
        f"Spostato dal {prima.astimezone(ROMA).strftime(FORMATO_DATA)} "
        f"al {post.data_ora.astimezone(ROMA).strftime(FORMATO_DATA)}"
    )
    campagne.registra_decisione(
        db,
        campagne.campagna(db, post.campagna_id),
        utente_id,
        "riprogrammato",
        motivo=None,
        nota=nota,
        foto_segnate=[],
        post_id=post.id,
    )
    return post


def annulla(db: Session, post_id: int, utente_id: int, nota: str, adesso: datetime):
    """Annulla un post approvato con la nota, senza sospendere la campagna (R-36, CA-85).

    La nota vuota dà 422 prima di ogni altro controllo; i controlli di stato
    (``annulla`` ammesso: campagna attiva o sospesa, post esce tra almeno 15
    minuti) sono in ``contenuti.annulla_un_post()``. Registra la decisione
    ``post_annullato`` con il post e la nota.
    """
    nota = nota.strip()
    if not nota:
        raise DatiNonValidi("Per annullare un post serve la nota.")
    post = contenuti.annulla_un_post(db, post_id, adesso)
    campagne.registra_decisione(
        db,
        campagne.campagna(db, post.campagna_id),
        utente_id,
        "post_annullato",
        motivo=None,
        nota=nota,
        foto_segnate=[],
        post_id=post.id,
    )
    return post


# Congelato per l'MVP, ADR-114: non estendere.
def controllato(
    db: Session, post_id: int, utente_id: int, valore: bool, adesso: datetime
):
    """Mette o toglie la spunta «va bene» sul post (R-30, CA-65).

    Solo in ``in_revisione`` su un post ``da_approvare`` senza intervento in
    corso; su un post ``da_rivedere`` la spunta non si mette (409).
    """
    return contenuti.segna_controllato(db, post_id, utente_id, valore, adesso)


def rigenera(
    db: Session,
    post_id: int,
    modalita: str,
    testo_proposto: str | None,
    nota: str | None,
    adesso: datetime,
) -> None:
    """Accende l'intervento in corso e accoda il job ``rigenera_post`` (R-03, R-31).

    ``contenuti.accendi_intervento()`` fa i controlli di R-16, R-31 e R-03:
    campagna non in revisione, post non da approvare, intervento già in corso
    o 3 rigenerazioni già fatte → 409. Il job scrive la nuova versione con le
    stesse foto; testo proposto e nota viaggiano negli argomenti del job.
    """
    tipo = MODALITA_RIGENERAZIONE.get(modalita)
    if tipo is None:
        raise DatiNonValidi("Modalità di rigenerazione non valida.")
    proposto = (testo_proposto or "").strip() or None
    if tipo == "rigenera_totale":
        proposto = None
    elif proposto is None:
        raise DatiNonValidi("Per rigenerare da un testo serve il testo proposto.")
    contenuti.accendi_intervento(db, post_id, tipo, adesso)
    accoda(
        RIGENERA_POST,
        post_id=post_id,
        testo_proposto=proposto,
        nota=(nota or "").strip() or None,
    )


def riprogramma(
    db: Session, post_id: int, utente_id: int, data_ora: datetime, adesso: datetime
):
    """Un post ``fallito`` torna ``approvato`` con una nuova data (R-34, CA-67).

    I controlli (``riprogramma`` ammesso: post ``fallito`` in campagna attiva o
    sospesa; data nel periodo e almeno 15 minuti dopo ``adesso``) sono in
    ``contenuti.riprogramma_post()``; qui si registra la decisione
    ``riprogrammato`` con il post interessato.
    """
    post = contenuti.riprogramma_post(db, post_id, data_ora, adesso)
    campagne.registra_decisione(
        db,
        campagne.campagna(db, post.campagna_id),
        utente_id,
        "riprogrammato",
        motivo=None,
        nota=None,
        foto_segnate=[],
        post_id=post.id,
    )
    return post
