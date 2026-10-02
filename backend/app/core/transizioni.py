"""
Funzione comune per la verifica delle transizioni di stato.

Usata da tutti i moduli per garantire che le transizioni
siano valide secondo le regole definite nei domain.py.
"""

from typing import Any, Set
from app.core.errori import TransizioneNonValida


def verifica_transizione(
    stato_corrente: str,
    nuovo_stato: str,
    transizioni_ammesse: Set[tuple[str, str]],
    contesto: str = "",
) -> None:
    """
    Verifica che una transizione di stato sia valida.

    Args:
        stato_corrente: Stato attuale
        nuovo_stato: Nuovo stato desiderato
        transizioni_ammesse: Set di tuple (stato_da, stato_a) ammesse
        contesto: Descrizione del contesto per il messaggio di errore

    Raises:
        TransizioneNonValida: Se la transizione non è ammessa
    """
    if (stato_corrente, nuovo_stato) not in transizioni_ammesse:
        msg = f"Transizione non valida: {stato_corrente} → {nuovo_stato}"
        if contesto:
            msg += f" ({contesto})"
        raise TransizioneNonValida(msg)
