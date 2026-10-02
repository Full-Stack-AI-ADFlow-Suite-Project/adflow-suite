"""
Orologio: fornisce l'ora corrente in UTC.

La funzione adesso() è iniettabile per i test, permettendo di
controllare il tempo nei test senza dipendere dall'orologio di sistema.
"""

from datetime import datetime, timezone
from typing import Callable


_adesso_impl: Callable[[], datetime] = lambda: datetime.now(timezone.utc)


def adesso() -> datetime:
    """
    Restituisce l'ora corrente in UTC.

    Returns:
        datetime: Timestamp corrente in UTC
    """
    return _adesso_impl()


def imposta_adesso(fn: Callable[[], datetime]):
    """
    Imposta un'implementazione personalizzata di adesso() per i test.

    Args:
        fn: Funzione che restituisce un datetime
    """
    global _adesso_impl
    _adesso_impl = fn


def ripristina_adesso():
    """Ripristina l'implementazione originale di adesso()."""
    global _adesso_impl
    _adesso_impl = lambda: datetime.now(timezone.utc)
