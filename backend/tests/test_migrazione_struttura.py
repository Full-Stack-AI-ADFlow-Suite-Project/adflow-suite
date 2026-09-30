"""
Test per verificare la struttura della migrazione senza database.
"""
import ast
import os


def test_migrazione_esiste():
    """Verifica che il file di migrazione esista."""
    migrazione_path = "alembic/versions/001_crea_tabelle_utente_sessione.py"
    assert os.path.exists(migrazione_path), "File di migrazione non trovato"


def test_migrazione_upgrade_downgrade():
    """Verifica che la migrazione abbia funzioni upgrade e downgrade."""
    migrazione_path = "alembic/versions/001_crea_tabelle_utente_sessione.py"
    
    with open(migrazione_path, 'r') as f:
        content = f.read()
    
    # Verifica che ci siano le funzioni upgrade e downgrade
    assert "def upgrade() -> None:" in content
    assert "def downgrade() -> None:" in content
    
    # Verifica che ci siano le tabelle utente e sessione
    assert "create_table('utente'" in content or "op.create_table" in content and "'utente'" in content
    assert "create_table('sessione'" in content or "op.create_table" in content and "'sessione'" in content
    
    # Verifica revision ID
    assert "revision: str = '001'" in content
    assert "down_revision: Union[str, None] = None" in content


def test_models_esistono():
    """Verifica che i models esistano."""
    assert os.path.exists("app/models.py"), "File models.py non trovato"
    
    with open("app/models.py", 'r') as f:
        content = f.read()
    
    # Verifica che ci siano le classi Utente e Sessione
    assert "class Utente(Base):" in content
    assert "class Sessione(Base):" in content
    
    # Verifica campi utente
    assert "email" in content
    assert "password_hash" in content
    assert "nome" in content
    assert "ruolo" in content
    assert "attivo" in content
    
    # Verifica campi sessione
    assert "token_hash" in content
    assert "utente_id" in content
    assert "scade_il" in content
