"""Durate R-29 per ruolo e configurazione, con ora UTC iniettata."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.config import leggi_impostazioni
from app.core.errori import NonAutenticato
from app.moduli.accesso import service
from app.moduli.accesso.models import Sessione
from tests.moduli.accesso.fabbrica import PASSWORD_DI_PROVA, utente

ORA = datetime(2026, 10, 8, 10, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "ruolo,durata",
    [
        ("artigiano", timedelta(days=7)),
        ("operatore", timedelta(hours=12)),
        ("admin", timedelta(hours=12)),
    ],
)
def test_login_durata_per_ruolo(db, ruolo, durata):
    record = utente(db, ruolo)
    service.login(db, record.email, PASSWORD_DI_PROVA, ORA)
    assert db.scalar(select(Sessione.scade_il)) == ORA + durata


@pytest.mark.parametrize("ruolo", ["artigiano", "operatore", "admin"])
def test_login_usa_durate_configurate(db, monkeypatch, ruolo):
    impostazioni = leggi_impostazioni()
    monkeypatch.setattr(impostazioni, "sessione_artigiano_giorni", 3)
    monkeypatch.setattr(impostazioni, "sessione_operatore_ore", 2)
    record = utente(db, ruolo)
    service.login(db, record.email, PASSWORD_DI_PROVA, ORA)
    durata = timedelta(days=3) if ruolo == "artigiano" else timedelta(hours=2)
    assert db.scalar(select(Sessione.scade_il)) == ORA + durata


def test_login_ruolo_corrotto_non_crea_sessione(db):
    record = utente(db, ruolo="superadmin")
    with pytest.raises(NonAutenticato):
        service.login(db, record.email, PASSWORD_DI_PROVA, ORA)
    assert db.scalar(select(Sessione)) is None


def test_me_non_accetta_ruolo_corrotto(db):
    record = utente(db)
    _, token = service.login(db, record.email, PASSWORD_DI_PROVA, ORA)
    record.ruolo = "superadmin"
    db.flush()
    with pytest.raises(NonAutenticato):
        service.utente_della_sessione(db, token, ORA)
