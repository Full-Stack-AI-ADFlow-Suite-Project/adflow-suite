# Congelato per l'MVP, ADR-114: non estendere.
"""Tipi di notifica, destinatari e stati di invio (plan §2, spec R-32)."""

ARTIGIANO = "artigiano"
OPERATORI = "operatori"

# tipo → chi la riceve. Il tipo decide il destinatario: chi chiama
# ``notifiche.crea()`` non lo sceglie, indica solo l'artigiano se serve.
DESTINATARI: dict[str, str] = {
    # Sprint 2b
    "campagna_pronta": OPERATORI,
    "piano_da_rivedere": OPERATORI,
    "generazione_fallita": OPERATORI,
    "post_fallito": OPERATORI,
    "campagna_respinta": ARTIGIANO,
    "campagna_scaduta": ARTIGIANO,
    # Sprint 3 (sospensione per account scaduto, R-07) e 4 (riepilogo, R-39)
    "campagna_sospesa": OPERATORI,
    "campagna_conclusa": ARTIGIANO,
}
TIPI = tuple(DESTINATARI)
# Le notifiche di un post si distinguono per ``post_id``.
TIPI_DI_UN_POST = ("post_fallito",)

CANALE_EMAIL = "email"
CANALI = (CANALE_EMAIL,)

DA_INVIARE = "da_inviare"
INVIATA = "inviata"
FALLITA = "fallita"
STATI_INVIO = (DA_INVIARE, INVIATA, FALLITA)
