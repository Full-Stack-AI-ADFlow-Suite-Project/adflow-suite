"""Stati, transizioni e valori ammessi del post (plan §2)."""

DA_APPROVARE = "da_approvare"
APPROVATO = "approvato"
PUBBLICATO = "pubblicato"
FALLITO = "fallito"
SCADUTO = "scaduto"
SCARTATO = "scartato"

# stato → stati ammessi; si usa con core.transizioni.verifica_transizione().
# da_rivedere è un indicatore (campo bool del post), non uno stato.
TRANSIZIONI: dict[str, frozenset[str]] = {
    DA_APPROVARE: frozenset({APPROVATO, SCADUTO, SCARTATO}),
    APPROVATO: frozenset({PUBBLICATO, FALLITO}),
    FALLITO: frozenset({APPROVATO}),
    PUBBLICATO: frozenset(),
    SCADUTO: frozenset(),
    SCARTATO: frozenset(),
}
STATI = tuple(TRANSIZIONI)

# Esiti che la pubblicazione può segnare su un post (segna_esito).
ESITI_PUBBLICAZIONE = (PUBBLICATO, FALLITO)

TIPI_INTERVENTO = (
    "generazione",
    "rigenera_totale",
    "rigenera_da_proposta",
    "ritocco_foto",
    "scelta_foto",
)
