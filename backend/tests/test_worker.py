"""
Test per il worker (worker.py).
"""

import pytest
from app.worker import tick_pubblicazione


@pytest.mark.asyncio
async def test_tick_pubblicazione_stub_vuoto():
    """
    Test che il job tick_pubblicazione esista e sia eseguibile.
    Per ora è uno stub vuoto, quindi deve solo non fallire.
    Quando T1-43 sarà completato, questo test dovrà essere aggiornato
    per verificare che chiami pubblicazione.pubblica_dovuti().
    """
    await tick_pubblicazione()
    # Se arriva qui senza eccezioni, il test passa
