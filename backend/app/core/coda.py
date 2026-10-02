"""Nomi dei job e funzione di accodamento (plan §4).

Ogni modulo importa la costante del job che vuole accodare e chiama
``accoda(nome, ...)`` senza importare il modulo destinatario
(constitution §2.5). In questo modo i moduli restano disaccoppiati:
campagne accoda un job di contenuti senza importare contenuti.

L'implementazione di ``accoda`` arriva con T1-05 (Procrastinate).
I nomi sono stringhe semplici: Procrastinate le usa come identificatori
univoci, quindi non devono mai cambiare una volta che il sistema è
in produzione con dati reali.
"""

from typing import Any

# ---------------------------------------------------------------------------
# Nomi dei job (plan §4).
# Usare sempre queste costanti: mai stringhe letterali nei moduli.
# ---------------------------------------------------------------------------

# Sprint 1
GENERA_CAMPAGNA = "genera_campagna"
TICK_PUBBLICAZIONE = "tick_pubblicazione"

# Sprint 2b
RIGENERA_POST = "rigenera_post"
INVIA_NOTIFICA = "invia_notifica"

# Sprint 3
RITOCCA_FOTO = "ritocca_foto"
PROMEMORIA = "promemoria"

# Sprint 4
RACCOGLI_METRICHE = "raccogli_metriche"
REPORT_SETTIMANALE = "report_settimanale"


def accoda(nome: str, **kwargs: Any) -> None:
    """Accoda un job per nome senza importare il modulo destinatario.

    Il chiamante usa una costante di questo modulo come ``nome`` e passa
    gli argomenti del job come keyword arguments. Esempio::

        from app.core.coda import accoda, GENERA_CAMPAGNA
        accoda(GENERA_CAMPAGNA, campagna_id=42)

    Args:
        nome: costante che identifica il job (es. ``GENERA_CAMPAGNA``).
              Non usare stringhe letterali: usare le costanti del modulo.
        **kwargs: argomenti specifici del job (es. ``campagna_id=42``).
                  Il tipo e la validità dipendono dal job chiamato.

    Raises:
        NotImplementedError: il corpo viene scritto in T1-05 con
            Procrastinate. Chiamare questa funzione prima di T1-05
            causa un errore esplicito e intenzionale.
    """
    raise NotImplementedError  # implementazione in T1-05
