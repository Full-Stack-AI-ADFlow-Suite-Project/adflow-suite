"""Valori ammessi del profilo della bottega (plan §2)."""

TIPI_PRODOTTO = (
    "legno_mobili",
    "ceramica_vetro",
    "gioielli_metalli",
    "tessile_pelle",
    "alimentare",
    "altro",
)
VALORI = (
    "artigianalita",
    "sostenibilita",
    "tradizione",
    "innovazione",
    "territorio",
    "su_misura",
)
FASCE_PREZZO = ("accessibile", "media", "alta")
OBIETTIVI = ("vendere", "negozio", "notorieta", "fidelizzare")
TONI = ("caldo", "elegante", "diretto", "ironico", "professionale")
CORTESIE = ("tu", "lei", "dipende")
CANALI = ("facebook", "instagram")

# frequenza → post alla settimana
POST_A_SETTIMANA = {"f1_2": 2, "f3_4": 3, "f5_piu": 5, "decidete_voi": 3}
FREQUENZE = tuple(POST_A_SETTIMANA)

CANALI_SOCIAL_ESISTENTI = ("facebook", "instagram", "nessuno")
FOTO_QUANTITA_MESE = ("meno_5", "da5_a12", "da12_a20", "oltre_20")
FOTO_CHI_SCATTA = ("artigiano", "fotografo", "consorzio")
FOTO_PERSONE = ("mai", "con_consenso", "spesso")
TIPI_EVENTO = (
    "fiera_mercatino",
    "festivita",
    "lancio_prodotto",
    "promozione",
    "chiusura",
    "altro",
)

# Campi senza i quali il profilo non si salva.
OBBLIGATORI = (
    "nome",
    "referente",
    "citta",
    "tipo_prodotto",
    "clienti_ideali",
    "obiettivo",
    "canali",
)

STATI_ACCOUNT = ("collegato", "scaduto", "scollegato")
