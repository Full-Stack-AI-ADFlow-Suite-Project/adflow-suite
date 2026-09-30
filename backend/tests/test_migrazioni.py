"""
Test per verificare le migrazioni Alembic.
Richiede PostgreSQL in esecuzione con i database adflow e adflow_test creati.
"""
import pytest
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text


def test_upgrade_downgrade():
    """Testa upgrade e downgrade delle migrazioni su database vuoto."""
    from app.config import settings

    # Usa database di test
    engine = create_engine(settings.database_url_test)

    # Pulisci database
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()

    # Configura Alembic
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url_test)

    # Test upgrade
    command.upgrade(alembic_cfg, "head")

    # Verifica che le tabelle siano state create
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name IN ('utente', 'sessione')"
        ))
        tables = [row[0] for row in result]
        assert "utente" in tables
        assert "sessione" in tables

    # Test downgrade
    command.downgrade(alembic_cfg, "base")

    # Verifica che le tabelle siano state rimosse
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name IN ('utente', 'sessione')"
        ))
        tables = [row[0] for row in result]
        assert "utente" not in tables
        assert "sessione" not in tables
