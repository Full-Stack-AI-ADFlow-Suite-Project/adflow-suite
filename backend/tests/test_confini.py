"""
Test dei confini tra moduli.

Verifica che i moduli non importino ciò che non devono importare
secondo constitution §2:
- Un modulo importa da un altro modulo solo service (e gli schemi che restituisce)
- Mai models, router, jobs altrui
- Solo se l'altro lo precede nell'ordine
"""

import ast
import importlib.util
from pathlib import Path


def get_imports_from_file(filepath: Path) -> list[str]:
    """Estrae gli import da un file Python."""
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
    return imports


def test_confini_moduli():
    """
    Test che verifica i confini tra moduli.

    TODO: Implementare completamente quando i moduli avranno codice.
    Per ora questo test è un placeholder.
    """
    # Ordine dei moduli: accesso, notifiche, artigiani, campagne, contenuti, revisione, pubblicazione
    # Questa funzione verrà implementata per verificare che:
    # - Un modulo non importi models, router, jobs di un altro modulo
    # - Un modulo importi solo service di moduli che lo precedono

    # Placeholder: il test passa per ora
    assert True
