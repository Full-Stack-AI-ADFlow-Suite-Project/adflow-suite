"""Controllo dei cambi di stato (constitution §1.8)."""

from collections.abc import Collection, Mapping

from app.core.errori import StatoNonValido


def verifica_transizione(
    transizioni: Mapping[str, Collection[str]], da: str, a: str
) -> None:
    """Solleva StatoNonValido se `transizioni` (dal domain.py del modulo) non ammette da → a."""
    if a not in transizioni.get(da, ()):
        raise StatoNonValido(f"Passaggio di stato non ammesso: da {da} a {a}.")
