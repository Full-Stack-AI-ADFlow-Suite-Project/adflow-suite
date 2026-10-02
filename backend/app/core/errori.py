"""Errori dei service: main.py li trasforma in {"detail": "messaggio"}."""


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
