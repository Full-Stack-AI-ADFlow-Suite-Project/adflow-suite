"""Stati, transizioni e valori ammessi della campagna (plan §2)."""

BOZZA = "bozza"
INVIATA = "inviata"
IN_GENERAZIONE = "in_generazione"
GENERAZIONE_FALLITA = "generazione_fallita"
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
    INVIATA: frozenset({IN_GENERAZIONE, SCADUTA}),
    IN_GENERAZIONE: frozenset({IN_REVISIONE, GENERAZIONE_FALLITA, SCADUTA}),
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

ORIGINI_FOTO = ("caricata", "creata_ai")

ESITO_APPROVATA = "approvata"
ESITO_RIMANDATA = "rimandata"
ESITO_RESPINTA = "respinta"
ESITI_DECISIONE = (ESITO_APPROVATA, ESITO_RIMANDATA, ESITO_RESPINTA)
MOTIVI_DECISIONE = ("foto", "altro")
