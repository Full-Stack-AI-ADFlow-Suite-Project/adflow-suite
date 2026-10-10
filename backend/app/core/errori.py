"""Errori dei service: main.py li trasforma in {"detail": "messaggio"}."""

from collections.abc import Iterable, Mapping
from typing import Any


class ErroreDominio(Exception):
    status_code: int = 500

    def __init__(self, messaggio: str) -> None:
        super().__init__(messaggio)
        self.messaggio = messaggio


class NonAutenticato(ErroreDominio):
    status_code = 401


class NonPermesso(ErroreDominio):
    status_code = 403


class NonTrovato(ErroreDominio):
    status_code = 404


class StatoNonValido(ErroreDominio):
    status_code = 409


class DatiNonValidi(ErroreDominio):
    status_code = 422


def frase_di_validazione(errori: Iterable[Mapping[str, Any]]) -> str:
    """La frase in italiano per un 422 dello schema (constitution §4).

    ``errori`` sono quelli di ``RequestValidationError.errors()``. Se un
    validatore di uno schema ha dato il suo messaggio (un ``ValueError``,
    scritto in italiano), la frase è quel messaggio: il primo. Altrimenti è
    «Dati non validi.» con i nomi dei campi da controllare. I valori ricevuti
    non entrano mai nella frase.
    """
    errori = list(errori)
    for errore in errori:
        causa = (errore.get("ctx") or {}).get("error")
        if errore.get("type") == "value_error" and isinstance(causa, ValueError):
            messaggio = str(causa).strip()
            if messaggio:
                return messaggio
    campi: list[str] = []
    for errore in errori:
        posizione = errore.get("loc") or ()
        # ("body", "titolo"), ("query", "stato"): il primo è da dove arriva.
        campo = posizione[1] if len(posizione) > 1 else None
        if isinstance(campo, str) and campo not in campi:
            campi.append(campo)
    if campi:
        return f"Dati non validi. Controllare: {', '.join(campi)}."
    return "Dati non validi."
