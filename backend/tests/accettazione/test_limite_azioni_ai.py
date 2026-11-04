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

from app.core.config import leggi_impostazioni
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


def test_una_raffica_di_rigenerazioni_incontra_un_limite(
    campagna_con_tanti_post, client, monkeypatch
):
    """Venti rigenerazioni di testo in pochi secondi: qualcuna deve dire 429.

    Il ciclo per post di R-03 (max 3) non è un limite di frequenza: qui si
    rigenerano 20 post diversi, ognuno la prima volta. Il limite si abbassa
    (il default, 20 al minuto, lascia lavorare un operatore vero).
    """
    monkeypatch.setattr(leggi_impostazioni(), "azioni_ai_limite", 5)
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
    primo_429 = codici.index(429)
    assert codici[:primo_429] == [200] * 5, codici


def test_il_429_dice_quando_riprovare(campagna_con_tanti_post, client, monkeypatch):
    monkeypatch.setattr(leggi_impostazioni(), "azioni_ai_limite", 1)
    url = f"/api/post/{campagna_con_tanti_post[0]}/rigenera"
    client.post(url, json={"modalita": "totale"})
    risposta = client.post(
        f"/api/post/{campagna_con_tanti_post[1]}/rigenera", json={"modalita": "totale"}
    )
    assert risposta.status_code == 429
    assert risposta.json()["detail"] == "Troppe richieste. Riprova tra poco."
    assert 1 <= int(risposta.headers["Retry-After"]) <= 60


def test_il_default_lascia_lavorare_un_operatore(campagna_con_tanti_post, client):
    """Con il limite di fabbrica (20 al minuto) venti rigenerazioni passano tutte."""
    codici = [
        client.post(f"/api/post/{p}/rigenera", json={"modalita": "totale"}).status_code
        for p in campagna_con_tanti_post
    ]
    assert 429 not in codici, codici


def test_con_il_database_giu_il_503_non_parla_di_accesso(
    campagna_con_tanti_post, client, monkeypatch
):
    """Il limite non raggiungibile: 503 con il messaggio del servizio, non del login."""
    from sqlalchemy.exc import OperationalError

    from app.core import limite_login

    class Guasto:
        def begin(self):
            raise OperationalError("istruzione", {}, Exception("database giù"))

    monkeypatch.setattr(limite_login, "motore", lambda: Guasto())
    risposta = client.post(
        f"/api/post/{campagna_con_tanti_post[0]}/rigenera", json={"modalita": "totale"}
    )
    assert risposta.status_code == 503
    assert risposta.json() == {
        "detail": "Servizio momentaneamente non disponibile. Riprova tra poco."
    }
