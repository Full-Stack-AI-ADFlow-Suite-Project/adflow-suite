"""
Errori comuni dell'applicazione.
"""


class AdFlowError(Exception):
    """Base exception per gli errori di AdFlow."""


class TransizioneNonValida(AdFlowError):
    """Eccezione quando una transizione di stato non è valida."""


class RisorsaNonTrovata(AdFlowError):
    """Eccezione quando una risorsa non viene trovata."""


class PermessoNegato(AdFlowError):
    """Eccezione quando un utente non ha i permessi necessari."""


class DatoNonValido(AdFlowError):
    """Eccezione quando i dati forniti non sono validi."""


class Conflitto(AdFlowError):
    """Eccezione quando c'è un conflitto (es. stato non valido, risorsa già esistente)."""
