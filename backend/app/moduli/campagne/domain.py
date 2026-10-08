"""Stati, transizioni e valori ammessi della campagna (plan §2)."""

BOZZA = "bozza"
INVIATA = "inviata"
IN_GENERAZIONE = "in_generazione"
GENERAZIONE_FALLITA = "generazione_fallita"
PIANO_DA_RIVEDERE = "piano_da_rivedere"
IN_REVISIONE = "in_revisione"
RESPINTA = "respinta"
SCADUTA = "scaduta"
ATTIVA = "attiva"
SOSPESA = "sospesa"
ANNULLATA = "annullata"
CONCLUSA = "conclusa"

# stato → stati ammessi; si usa con core.transizioni.verifica_transizione().
TRANSIZIONI: dict[str, frozenset[str]] = {
    BOZZA: frozenset({INVIATA}),
    INVIATA: frozenset({IN_GENERAZIONE, GENERAZIONE_FALLITA, SCADUTA}),
    IN_GENERAZIONE: frozenset(
        {IN_REVISIONE, PIANO_DA_RIVEDERE, GENERAZIONE_FALLITA, SCADUTA}
    ),
    PIANO_DA_RIVEDERE: frozenset({IN_GENERAZIONE, RESPINTA, SCADUTA}),
    GENERAZIONE_FALLITA: frozenset({INVIATA, SCADUTA}),
    IN_REVISIONE: frozenset({ATTIVA, RESPINTA, SCADUTA}),
    ATTIVA: frozenset({CONCLUSA, SOSPESA, ANNULLATA}),
    SOSPESA: frozenset({ATTIVA, ANNULLATA}),
    RESPINTA: frozenset(),
    SCADUTA: frozenset(),
    ANNULLATA: frozenset(),
    CONCLUSA: frozenset(),
}
STATI = tuple(TRANSIZIONI)

STATI_CHIUSI = (CONCLUSA, RESPINTA, SCADUTA, ANNULLATA)
ORIGINI_GRUPPO = ("caricate", "create_ai")
ORIGINI_FOTO = ("caricata", "creata_ai", "cartolina")
TIPI_CONTENUTO = (
    "pezzo_finito",
    "dettaglio",
    "lavorazione",
    "persona",
    "ambientato",
    "evento",
)

ESITO_APPROVATA = "approvata"
ESITO_NOTA = "nota"
ESITO_RESPINTA = "respinta"
ESITI_DECISIONE = (
    ESITO_APPROVATA,
    ESITO_RESPINTA,
    "proseguita",
    "canale_tolto",
    ESITO_NOTA,
    "sospesa",
    "riattivata",
    "annullata",
    "riprogrammato",
)
MOTIVI_DECISIONE = ("foto", "altro")
