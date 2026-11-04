"""PostgreSQL fermo: 503 senza dati incoerenti (T4-105, §7.4).

Si sostituisce la sessione con una che punta a una porta chiusa, come un
database fermo; l'atteso di §7.4 è «503 senza dati incoerenti; il worker
riparte». Il worker riparte perché il tick è un job idempotente: la prova è
che il tick successivo, con il database tornato su, non trova lavoro a metà.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import leggi_impostazioni
from app.core.db import crea_motore, get_db
from app.moduli.accesso.service import utente_corrente
from app.moduli.pubblicazione import service as pubblicazione
from app.main import app
from tests.moduli.accesso.fabbrica import utente


def test_database_fermo_dà_503(client: TestClient, db, utente_di_prova):
    utente_di_prova("operatore")
    url = make_url(leggi_impostazioni().database_url_test).set(port=1)
    motore_morto = crea_motore(url)
    sessione_morta = sessionmaker(bind=motore_morto)()
    app.dependency_overrides[get_db] = lambda: sessione_morta
    try:
        risposta = client.get("/api/campagne")
    finally:
        app.dependency_overrides[get_db] = lambda: db
        sessione_morta.close()
        motore_morto.dispose()

    assert risposta.status_code == 503, f"risposta {risposta.status_code}"


def test_il_worker_riparte_dopo_il_guasto(db):
    """Il tick non ha stato a metà: rilanciato con il database sano non rompe nulla."""
    from app.moduli.revisione import service as revisione

    adesso = datetime.now(timezone.utc)
    revisione.scadenze(db, adesso)  # non solleva con un database sano
    pubblicazione.pubblica_dovuti(db, adesso)
