"""Sospendi, riattiva e annulla una campagna (spec R-33, plan §3).

Gli endpoint di ``router.py`` chiamano queste funzioni: lo stato della
campagna cambia solo con ``campagne.cambia_stato()``, quello dei post solo
con ``contenuti`` (plan §6, constitution §1). Ogni azione registra la sua
decisione. In campagna attiva o sospesa sono le uniche azioni ammesse, con
la riprogrammazione di un post fallito (R-16).
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.errori import DatiNonValidi, StatoNonValido
from app.moduli.accesso import service as accesso
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti


def sospendi(db: Session, campagna_id: int, utente: accesso.Utente) -> None:
    """Attiva → sospesa: il tick smette di pubblicare (R-33, CA-32).

    I post ``approvato`` restano tali: alla riattivazione quelli in arretrato
    si pubblicano o si annullano, gli altri escono alla loro data.

    Raises:
        NonTrovato: campagna che non esiste (404).
        StatoNonValido: la campagna non è ``attiva`` (409).
    """
    record = campagne.campagna(db, campagna_id)
    if record.stato != "attiva":
        raise StatoNonValido("Si sospende solo una campagna attiva.")
    campagne.registra_decisione(
        db, record, utente.id, "sospesa", motivo=None, nota=None, foto_segnate=[]
    )
    campagne.cambia_stato(db, record, "sospesa")


def riattiva(
    db: Session,
    campagna_id: int,
    utente: accesso.Utente,
    pubblica_ora: list[int],
    adesso: datetime,
) -> None:
    """Sospesa → attiva; gli arretrati non scelti diventano ``annullato`` (R-33).

    I post in arretrato (``approvato`` con la data già passata) in
    ``pubblica_ora`` tornano pubblicabili al primo tick dopo la
    riattivazione; gli altri arretrati si annullano e non escono più (CA-32).

    Raises:
        NonTrovato: campagna che non esiste (404).
        StatoNonValido: la campagna non è ``sospesa`` (409).
        DatiNonValidi: ``pubblica_ora`` contiene un post non in arretrato (422).
    """
    record = campagne.campagna(db, campagna_id)
    if record.stato != "sospesa":
        raise StatoNonValido("Si riattiva solo una campagna sospesa.")
    arretrati = {
        post.id
        for post in contenuti.post_della_campagna(db, campagna_id)
        if post.stato == "approvato" and post.data_ora <= adesso
    }
    scelti = set(pubblica_ora)
    if not scelti <= arretrati:
        raise DatiNonValidi(
            "Si possono pubblicare subito solo post approvati con la data passata."
        )
    contenuti.annulla_post(db, campagna_id, post_ids=arretrati - scelti)
    campagne.registra_decisione(
        db, record, utente.id, "riattivata", motivo=None, nota=None, foto_segnate=[]
    )
    campagne.cambia_stato(db, record, "attiva")


def annulla(
    db: Session, campagna_id: int, utente: accesso.Utente, adesso: datetime
) -> None:
    """Attiva o sospesa → annullata: i post ``approvato`` diventano ``annullato``.

    Un post ``annullato`` è chiuso e non si pubblica (R-33); la campagna è
    chiusa e ``chiusa_il`` prende ``adesso`` (CA-32).

    Raises:
        NonTrovato: campagna che non esiste (404).
        StatoNonValido: la campagna non è ``attiva`` né ``sospesa`` (409).
    """
    record = campagne.campagna(db, campagna_id)
    if record.stato not in ("attiva", "sospesa"):
        raise StatoNonValido("Si annulla solo una campagna attiva o sospesa.")
    contenuti.annulla_post(db, campagna_id)
    campagne.registra_decisione(
        db, record, utente.id, "annullata", motivo=None, nota=None, foto_segnate=[]
    )
    campagne.cambia_stato(db, record, "annullata", ora=adesso)
