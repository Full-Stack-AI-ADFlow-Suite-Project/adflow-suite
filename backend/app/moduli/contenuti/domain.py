"""Stati, transizioni e valori ammessi del post (plan §2)."""

DA_APPROVARE = "da_approvare"
APPROVATO = "approvato"
PUBBLICATO = "pubblicato"
FALLITO = "fallito"
SCADUTO = "scaduto"
SCARTATO = "scartato"
ANNULLATO = "annullato"

# stato → stati ammessi; si usa con core.transizioni.verifica_transizione().
# da_rivedere è un indicatore (campo bool del post), non uno stato.
TRANSIZIONI: dict[str, frozenset[str]] = {
    DA_APPROVARE: frozenset({APPROVATO, SCADUTO, SCARTATO}),
    APPROVATO: frozenset({PUBBLICATO, FALLITO, ANNULLATO}),
    FALLITO: frozenset({APPROVATO}),
    PUBBLICATO: frozenset(),
    SCADUTO: frozenset(),
    SCARTATO: frozenset(),
    ANNULLATO: frozenset(),
}
STATI = tuple(TRANSIZIONI)

# Esiti che la pubblicazione può segnare su un post (segna_esito).
ESITI_PUBBLICAZIONE = (PUBBLICATO, FALLITO)

TIPI_INTERVENTO = (
    "generazione",
    "rigenera_totale",
    "rigenera_da_proposta",
    "modifica_operatore",
    "ritocco_foto",
    "scelta_foto",
    "cambio_foto",
)

FORMATI_POST = ("singola", "carosello")
TIPI_RIEMPITIVO = ("archivio", "cartolina", "immagine_ai")
LIVELLI_VALIDATORE = ("blocco", "avviso")
TIPI_ERRORE_GENERAZIONE = (
    "temporaneo",
    "risposta",
    "configurazione",
    "richiesta",
    "rifiuto",
)
TIPI_INTERVENTO_IN_CORSO = ("rigenera_totale", "rigenera_da_proposta", "ritocco_foto")
STATI_CHIUSI = (PUBBLICATO, FALLITO, ANNULLATO, SCARTATO, SCADUTO)

# Numeri di prova stabiliti da R-21. Proporzioni e link_cliccabili attendono
# i valori concordati dal team: plan §2 li richiede, R-21 non li definisce.
SCHEDE_CANALE = {
    "facebook": {
        "max_caratteri": 500,
        "max_hashtag": 3,
        "limite_caratteri": 5000,
        "limite_hashtag": 30,
        "max_foto": 10,
    },
    "instagram": {
        "max_caratteri": 600,
        "max_hashtag": 5,
        "limite_caratteri": 2200,
        "limite_hashtag": 30,
        "max_foto": 10,
    },
}
