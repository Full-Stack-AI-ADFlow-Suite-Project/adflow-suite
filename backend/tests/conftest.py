"""
Configurazione pytest con fixture comuni.
"""

import pytest
from app.core.orologio import ripristina_adesso


@pytest.fixture(autouse=True)
def ripristina_orologio():
    """
    Fixture automatica che ripristina l'orologio dopo ogni test.
    Assicura che i test non influenzino l'orologio tra loro.
    """
    yield
    ripristina_adesso()
