"""Isolamento dei contatori persistenti e indirizzi riservati delle fixture."""
import pytest
from sqlalchemy import text
from app.core import limite_login
from app.core.config import leggi_impostazioni


@pytest.fixture(autouse=True)
def sicurezza_accesso_test(motore_test, monkeypatch):
    monkeypatch.setattr(limite_login, "motore", lambda: motore_test)
    monkeypatch.setattr(leggi_impostazioni(), "email_test_environment", True)
    with motore_test.begin() as c:
        c.execute(text("DELETE FROM limite_login"))
    yield
    with motore_test.begin() as c:
        c.execute(text("DELETE FROM limite_login"))
