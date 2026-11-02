"""Il limite di frequenza delle azioni che fanno spendere l'AI (T4-102, R-15).

Invio, Rigenera testo, Rigenera immagine e Rifai il post fanno partire
chiamate AI a pagamento. L'atteso, per un'app che espone queste azioni a un
operatore autenticato, è che un limite di frequenza dell'applicazione fermi
una raffica: oggi il limite esiste solo sul login (core/limite_login.py) e
questo test lo documenta finché non cambia.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.moduli.accesso.service import utente_corrente
from app.main import app
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare

N_RIGENERAZIONI = 20


@pytest.fixture
def campagna_con_tanti_post(db: Session, client: TestClient, utente_di_prova):
    """Una campagna in revisione con 20 post da approvare, e l'operatore dentro."""
    operatore = utente_di_prova("operatore")
    bottega = profilo(db)
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    post = [
        post_da_approvare(db, campagna_id=campagna.id) for _ in range(N_RIGENERAZIONI)
    ]
    db.flush()
    return [p.id for p in post]


@pytest.mark.xfail(
    strict=True,
    reason="RL-018 (R-15): nessun limite di frequenza sulle azioni che fanno "
    "partire chiamate AI a pagamento (invio, rigenera testo, rigenera "
    "immagine, rifai il post): 20 richieste in pochi secondi passano tutte",
)
def test_una_raffica_di_rigenerazioni_incontra_un_limite(
    campagna_con_tanti_post, client
):
    """Venti rigenerazioni di testo in pochi secondi: qualcuna deve dire 429.

    Il ciclo per post di R-03 (max 3) non è un limite di frequenza: qui si
    rigenerano 20 post diversi, ognuno la prima volta.
    """
    codici = []
    for post_id in campagna_con_tanti_post:
        risposta = client.post(
            f"/api/post/{post_id}/rigenera", json={"modalita": "totale"}
        )
        codici.append(risposta.status_code)
    assert any(codice == 429 for codice in codici), (
        f"nessun limite di frequenza ha risposto su {N_RIGENERAZIONI} richieste "
        f"consecutive: {codici}"
    )
