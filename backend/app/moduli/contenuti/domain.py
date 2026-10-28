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
    "rigenera_immagine",
)

FORMATI_POST = ("singola", "carosello")
TIPI_RIEMPITIVO = ("archivio", "cartolina", "immagine_ai")
IMMAGINE_AI = "immagine_ai"
# Il codice, non l'AI, la aggiunge in fondo al testo di un post con immagine AI (R-43).
DICITURA_IMMAGINE_AI = "Immagine creata con AI"
LIVELLI_VALIDATORE = ("blocco", "avviso")
TIPI_ERRORE_GENERAZIONE = (
    "temporaneo",
    "risposta",
    "configurazione",
    "richiesta",
    "rifiuto",
)
# Gli esiti di una chiamata all'AI: riuscita, oppure il tipo dell'errore (R-35, R-50).
ESITI_CHIAMATA_AI = ("ok",) + TIPI_ERRORE_GENERAZIONE
TIPI_INTERVENTO_IN_CORSO = (
    "rigenera_totale",
    "rigenera_da_proposta",
    "ritocco_foto",
    "rigenera_immagine",
)
STATI_CHIUSI = (PUBBLICATO, FALLITO, ANNULLATO, SCARTATO, SCADUTO)

# Interventi dell'operatore sul singolo post (spec R-16, R-30, R-34, R-36, R-49).
MODIFICA = "modifica"
RIGENERA = "rigenera"
RIGENERA_IMMAGINE = "rigenera_immagine"
CAMBIA_FOTO = "cambia_foto"
SPOSTA = "sposta"
ANNULLA = "annulla"
RIPROGRAMMA = "riprogramma"
INTERVENTI = (
    MODIFICA,
    RIGENERA,
    RIGENERA_IMMAGINE,
    CAMBIA_FOTO,
    SPOSTA,
    ANNULLA,
    RIPROGRAMMA,
)
# R-49: al massimo 3 rigenerazioni dell'immagine per post, contate a parte da R-03.
MAX_RIGENERAZIONI_IMMAGINE = 3

# (stato della campagna, stato del post) → interventi ammessi (spec R-16).
# Sui post APPROVATO vale anche il margine: il post esce tra almeno
# MARGINE_SLOT_MINUTI da adesso. Mai con un intervento in corso (R-31).
# Gli stati della campagna si scrivono per nome (plan §6).
INTERVENTI_AMMESSI: dict[tuple[str, str], frozenset[str]] = {
    ("in_revisione", DA_APPROVARE): frozenset(
        {MODIFICA, RIGENERA, RIGENERA_IMMAGINE, CAMBIA_FOTO, SPOSTA}
    ),
    ("attiva", APPROVATO): frozenset({MODIFICA, CAMBIA_FOTO, SPOSTA, ANNULLA}),
    ("sospesa", APPROVATO): frozenset({MODIFICA, CAMBIA_FOTO, SPOSTA, ANNULLA}),
    ("attiva", FALLITO): frozenset({RIPROGRAMMA}),
    ("sospesa", FALLITO): frozenset({RIPROGRAMMA}),
}
# Stati dei post che tengono occupata una foto sul loro canale (costituzione §1.9).
STATI_CHE_USANO_LA_FOTO = (DA_APPROVARE, APPROVATO, PUBBLICATO, FALLITO)

# Schede MVP (R-21): proporzioni come stringhe "larghezza:altezza", gli estremi
# dell'intervallo ammesso (4:5 – 1,91:1).
# Sono scelte del progetto, non tutti i formati supportati dalle piattaforme.
SCHEDE_CANALE = {
    "facebook": {
        "max_caratteri": 500,
        "max_hashtag": 3,
        "limite_caratteri": 5000,
        "limite_hashtag": 30,
        "max_foto": 10,
        "proporzioni": ("4:5", "1.91:1"),
        "link_cliccabili": True,
    },
    "instagram": {
        "max_caratteri": 600,
        "max_hashtag": 5,
        "limite_caratteri": 2200,
        "limite_hashtag": 30,
        "max_foto": 10,
        "proporzioni": ("4:5", "1.91:1"),
        "link_cliccabili": False,
    },
}
