"""Validazione comune dei testi degli schemi (RL-026).

PostgreSQL non accetta il byte NUL (``\\x00``) in una colonna testuale: il
rifiuto sta prima, nello schema di ingresso, e l'API risponde 422 con il
messaggio in italiano del validatore (``core/errori.frase_di_validazione``).
"""

from math import isfinite
from typing import Any


def verifica_testi(valore: Any) -> None:
    """Rifiuta NUL e testi non UTF-8, anche annidati in dizionari e liste.

    Gli altri tipi passano: serve a un validatore ``mode="before"`` su tutti i
    campi di uno schema, senza doverli elencare.

    Raises:
        ValueError: testo con il byte NUL o non codificabile in UTF-8, oppure
            numero non finito.
    """
    if isinstance(valore, str):
        if "\x00" in valore:
            raise ValueError("Caratteri non validi.")
        try:
            valore.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Caratteri non validi.") from None
    elif isinstance(valore, float) and not isfinite(valore):
        raise ValueError("Numero non valido.")
    elif isinstance(valore, dict):
        for chiave, elemento in valore.items():
            verifica_testi(chiave)
            verifica_testi(elemento)
    elif isinstance(valore, list):
        for elemento in valore:
            verifica_testi(elemento)
