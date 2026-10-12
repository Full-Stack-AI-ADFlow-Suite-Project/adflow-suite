"""Interventi dell'operatore sul singolo post (spec §3, plan §3).

Gli endpoint di ``router.py`` chiamano queste funzioni: stati e versioni del
post e intervento in corso sono di ``contenuti`` (plan §6), la decisione è di
``campagne`` e il job ``rigenera_post`` si accoda per nome. Regole: R-03, R-16
(solo in ``in_revisione``; in attiva o sospesa solo la riprogrammazione),
R-30, R-31, R-34.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.coda import RIGENERA_POST, accoda
from app.core.errori import DatiNonValidi
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti

# La modalità che arriva dall'API e il tipo che il post salva (R-31).
MODALITA_RIGENERAZIONE = {
    "totale": "rigenera_totale",
    "da_proposta": "rigenera_da_proposta",
}


def modifica(
    db: Session,
    post_id: int,
    utente_id: int,
    testo: str,
    hashtag: list[str],
    adesso: datetime,
):
    """Modifica a mano: nasce una versione ``modifica_operatore`` (R-30, CA-64).

    I controlli (campagna ``in_revisione``, post ``da_approvare``, nessun
    intervento in corso, testo diverso e senza blocchi) sono in
    ``contenuti.modifica_post()``: 404, 409 e 422 escono da lì.
    """
    return contenuti.modifica_post(db, post_id, utente_id, testo, hashtag, adesso)


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

    È l'unico intervento sul singolo post che la campagna attiva o sospesa
    ammette (R-16). I controlli (post ``fallito``, campagna attiva o sospesa,
    data nel periodo e almeno 15 minuti dopo ``adesso``) sono in
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
