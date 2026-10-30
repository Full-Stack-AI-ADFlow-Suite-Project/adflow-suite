"""§1.5 — Il margine di 15 minuti e il divieto di AI dopo l'approvazione.

Attacchi di §4.3: intervento a 15:01 e a 14:59 dall'uscita; campagna sospesa;
nessuna AI dopo l'approvazione, Rigenera immagine compresa.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.ai import usa_ai
from app.adapters.ai.finto import AIFinto
from app.core.errori import StatoNonValido
from app.moduli.revisione import interventi
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_sospesa
from tests.moduli.contenuti.fabbrica import post_approvato


def _post_che_esce_tra(db, utente, minuti):
    bottega = profilo(db, utente_id=utente.id)
    campagna = campagna_attiva(db, profilo_id=bottega.id)
    post = post_approvato(
        db,
        campagna_id=campagna.id,
        data_ora=datetime.now(timezone.utc) + timedelta(minutes=minuti),
    )
    db.flush()
    return campagna, post


def test_intervento_a_15_minuti_e_uno_secondo_e_ammesso(db, utente_di_prova):
    """Il confine di R-16: 15:01 dall'uscita → la modifica a mano passa."""
    artigiano = utente_di_prova("artigiano")
    operatore = utente_di_prova("operatore")
    _, post = _post_che_esce_tra(db, artigiano, 15.0167)
    interventi.modifica(
        db,
        post.id,
        operatore,
        "Testo modificato al limite del margine",
        ["artigianato"],
        datetime.now(timezone.utc),
    )
    assert post.versione_corrente.testo.startswith("Testo modificato")


def test_intervento_a_14_minuti_e_59_e_rifiutato(db, utente_di_prova):
    """14:59 dall'uscita → 409, nessuna versione nuova."""
    artigiano = utente_di_prova("artigiano")
    operatore = utente_di_prova("operatore")
    _, post = _post_che_esce_tra(db, artigiano, 14.98)
    numero = post.versione_corrente.numero

    with pytest.raises(StatoNonValido):
        interventi.modifica(
            db,
            post.id,
            operatore,
            "Troppo tardi per modificare",
            ["artigianato"],
            datetime.now(timezone.utc),
        )
    assert post.versione_corrente.numero == numero


def test_su_una_campagna_sospesa_l_intervento_e_ammesso(db, utente_di_prova):
    """Sospesa + post approvato che esce tra più di 15 minuti: la modifica passa."""
    artigiano = utente_di_prova("artigiano")
    operatore = utente_di_prova("operatore")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_sospesa(db, profilo_id=bottega.id)
    post = post_approvato(
        db,
        campagna_id=campagna.id,
        data_ora=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.flush()
    interventi.modifica(
        db,
        post.id,
        operatore,
        "Testo cambiato con la campagna sospesa",
        ["artigianato"],
        datetime.now(timezone.utc),
    )
    assert post.versione_corrente.testo.startswith("Testo cambiato")


def test_nessuna_ai_dopo_l_approvazione(db, utente_di_prova):
    """Rigenera testo e Rigenera immagine su una campagna attiva → 409 (R-16)."""
    artigiano = utente_di_prova("artigiano")
    _, post = _post_che_esce_tra(db, artigiano, 30)
    operatore = utente_di_prova("operatore")

    finto = AIFinto()
    with usa_ai(finto):
        with pytest.raises(StatoNonValido):
            interventi.rigenera(
                db, post.id, "totale", None, None, datetime.now(timezone.utc)
            )
        with pytest.raises(StatoNonValido):
            interventi.rigenera_immagine(
                db, post.id, None, False, None, datetime.now(timezone.utc)
            )
    assert finto.chiamate == [], "l'AI è stata chiamata dopo l'approvazione"
