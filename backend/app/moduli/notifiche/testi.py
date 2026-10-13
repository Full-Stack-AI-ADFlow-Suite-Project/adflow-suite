# Congelato per l'MVP, ADR-114: non estendere.
"""Testi delle email delle notifiche (spec §4, R-18).

``notifiche`` precede ``campagne``: qui non arrivano dati di dominio, solo il
``contenuto`` preparato da chi ha creato la notifica (identificativi e testi,
come da architettura). Le chiavi del contenuto:

- ``titolo``: il titolo della campagna, per ogni tipo;
- ``motivo`` e ``nota``: la decisione dell'operatore, per ``campagna_respinta``;
- ``foto``: elenco di ``{"nome", "mime"}`` delle foto segnate da rifare, per
  ``campagna_respinta`` — i byte li carica l'invio dall'adattatore archivio;
- ``canale`` e ``data_ora``: il post che non è uscito, per ``post_fallito``;
- ``errore``: il tipo dell'ultimo errore, per ``generazione_fallita``.
"""

from app.core.config import leggi_impostazioni

from . import domain

_MOTIVI_RESPINTA = {"foto": "foto da rifare", "altro": "altro"}


def _firma() -> str:
    """Il contatto del consorzio chiude ogni email (spec R-29, ADR-102)."""
    impostazioni = leggi_impostazioni()
    righe = [impostazioni.consorzio_nome or "Il consorzio"]
    if impostazioni.consorzio_telefono:
        righe.append(f"Tel. {impostazioni.consorzio_telefono}")
    if impostazioni.consorzio_email:
        righe.append(impostazioni.consorzio_email)
    return "\n".join(righe)


def _titolo(contenuto: dict) -> str:
    return contenuto.get("titolo") or "la tua campagna"


def _operatori(tipo: str, contenuto: dict, destinatario: str) -> tuple[str, str] | None:
    titolo = _titolo(contenuto)
    if tipo == "campagna_pronta":
        return (
            f"Campagna pronta: {titolo}",
            f"Ciao {destinatario},\n\nla campagna «{titolo}» è pronta per la "
            f"revisione: piano e testi ti aspettano in «Campagne da approvare».",
        )
    if tipo == "piano_da_rivedere":
        return (
            f"Piano da rivedere: {titolo}",
            f"Ciao {destinatario},\n\nil piano della campagna «{titolo}» è "
            f"debole: aprila e decidi se proseguire o respingerla.",
        )
    if tipo == "generazione_fallita":
        errore = contenuto.get("errore")
        dettaglio = f" (errore: {errore})" if errore else ""
        return (
            f"Generazione fallita: {titolo}",
            f"Ciao {destinatario},\n\nla generazione della campagna "
            f"«{titolo}» non è riuscita{dettaglio}. Apri la campagna e usa "
            f"«Riprova».",
        )
    if tipo == "post_fallito":
        canale = contenuto.get("canale")
        data_ora = contenuto.get("data_ora")
        dettagli = []
        if canale:
            dettagli.append(f"canale {canale}")
        if data_ora:
            dettagli.append(f"in programma il {data_ora}")
        dettaglio = " (" + ", ".join(dettagli) + ")" if dettagli else ""
        return (
            f"Post non pubblicato: {titolo}",
            f"Ciao {destinatario},\n\nun post della campagna «{titolo}»"
            f"{dettaglio} non è stato pubblicato. Aprila e riprogrammalo.",
        )
    if tipo == "campagna_sospesa":
        return (
            f"Campagna sospesa: {titolo}",
            f"Ciao {destinatario},\n\nla campagna «{titolo}» è stata sospesa: "
            f"controlla l'account social da ricollegare.",
        )
    return None


def _artigiano(tipo: str, contenuto: dict, destinatario: str) -> tuple[str, str] | None:
    titolo = _titolo(contenuto)
    if tipo == "campagna_respinta":
        motivo = _MOTIVI_RESPINTA.get(
            contenuto.get("motivo") or "", contenuto.get("motivo") or "altro"
        )
        nota = (contenuto.get("nota") or "").strip()
        righe = [
            f"Ciao {destinatario},",
            "",
            f"il consorzio non ha approvato la campagna «{titolo}».",
            f"Motivo: {motivo}.",
        ]
        if nota:
            righe.append(f"Richiesta di modifica: «{nota}»")
        if contenuto.get("foto"):
            righe.append("In allegato trovi le foto da rifare.")
        righe += [
            "",
            "Tienine conto nella nuova campagna: foto e testi vanno "
            "inseriti di nuovo.",
        ]
        return (f"Campagna respinta: {titolo}", "\n".join(righe))
    if tipo == "campagna_scaduta":
        return (
            f"Campagna scaduta: {titolo}",
            f"Ciao {destinatario},\n\nla campagna «{titolo}» è scaduta: il "
            f"periodo è finito prima che i post venissero approvati. Puoi "
            f"creare una nuova campagna quando vuoi.",
        )
    if tipo == "campagna_conclusa":
        return (
            f"Campagna conclusa: {titolo}",
            f"Ciao {destinatario},\n\nla campagna «{titolo}» si è conclusa. "
            f"Grazie per averla affidata al consorzio.",
        )
    return None


def componi(tipo: str, contenuto: dict, destinatario: str) -> tuple[str, str]:
    """Oggetto e corpo dell'email per il tipo di notifica.

    Args:
        tipo: uno di ``domain.TIPI``.
        contenuto: i dati dell'evento passati da chi ha creato la notifica.
        destinatario: il nome di chi riceve l'email.

    Returns:
        ``(oggetto, corpo)`` in italiano, con la firma del consorzio.
    """
    composizione = (
        _artigiano if domain.DESTINATARI.get(tipo) == domain.ARTIGIANO else _operatori
    )
    risultato = composizione(tipo, contenuto, destinatario)
    if risultato is None:
        risultato = (
            "Nuova notifica AdFlow",
            f"Ciao {destinatario},\n\nc'è una novità sulla campagna "
            f"«{_titolo(contenuto)}»: accedi per vederla.",
        )
    oggetto, corpo = risultato
    return oggetto, f"{corpo}\n\n{_firma()}"
