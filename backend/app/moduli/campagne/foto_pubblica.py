"""Firma a tempo e indirizzo pubblico della foto per Instagram (T3-23, spec R-42, constitution §3).

Fornisce:
- Calcolo e verifica della firma crittografica HMAC-SHA256 con scadenza temporale;
- Generazione dell'URL pubblico firmato utilizzabile dai crawler/server di Meta/Instagram;
- Rispetto della difesa in profondità: confronto a tempo costante e rifiuto con 404 per
  qualsiasi alterazione, scadenza o anomalia, senza esporre dati interni.
"""

from datetime import datetime, timezone
import hashlib
import hmac
import os
from typing import Final
from urllib.parse import urlencode

from app.core.config import leggi_impostazioni
from app.core.errori import DatiNonValidi
from app.core.orologio import adesso

from .sistemazione_foto import PROPORZIONI_CANALE

# Scadenza predefinita della firma: 24 ore (86400 secondi)
DURATA_PREDEFINITA_SECONDI: Final[int] = 86400


def _segreto_firma() -> bytes:
    """Deriva una chiave segreta crittografica con domain separation per la firma delle foto."""
    impostazioni = leggi_impostazioni()
    base = impostazioni.login_limite_segreto.encode("utf-8")
    return hmac.new(
        base, b"adflow:campagne:foto_pubblica:hmac_sha256", hashlib.sha256
    ).digest()


def calcola_mac(foto_id: int, canale: str, scadenza_ts: int) -> str:
    """Calcola il codice esadecimale HMAC-SHA256 per la terna (foto_id, canale, scadenza_ts)."""
    segreto = _segreto_firma()
    canale_norm = canale.strip().lower()
    messaggio = f"{foto_id}:{canale_norm}:{scadenza_ts}".encode("utf-8")
    return hmac.new(segreto, messaggio, hashlib.sha256).hexdigest()


def componi_firma(foto_id: int, canale: str, scadenza_ts: int) -> str:
    """Compone la firma a tempo compatta nel formato: '{scadenza_ts}_{mac}'."""
    mac = calcola_mac(foto_id, canale, scadenza_ts)
    return f"{scadenza_ts}_{mac}"


def verifica_firma(
    foto_id: int,
    canale: str,
    firma: str,
    scadenza_ts: int | None = None,
    ora: datetime | None = None,
) -> bool:
    """Verifica che la firma sia valida e che il timestamp non sia scaduto.

    Supporta sia il formato compatto ('{scadenza_ts}_{mac}') sia il passaggio
    esplicito del parametro query 'scadenza_ts'.

    Restituisce False su qualsiasi manomissione, scadenza, canale non valido o
    anomalia di formato (garantendo anti-timing attack tramite compare_digest).
    """
    if foto_id <= 0 or not canale or not firma:
        return False

    canale_norm = canale.strip().lower()
    if canale_norm not in PROPORZIONI_CANALE:
        return False

    firma_str = firma.strip()
    mac_fornito: str
    ts_effettivo: int

    if "_" in firma_str:
        parti = firma_str.split("_", 1)
        try:
            ts_estratto = int(parti[0])
        except (ValueError, TypeError):
            return False
        if scadenza_ts is not None and scadenza_ts != ts_estratto:
            return False
        ts_effettivo = ts_estratto
        mac_fornito = parti[1]
    elif scadenza_ts is not None:
        ts_effettivo = scadenza_ts
        mac_fornito = firma_str
    else:
        return False

    if ts_effettivo <= 0:
        return False

    # Controllo scadenza rispetto all'istante di riferimento
    istante_riferimento = ora if ora is not None else adesso()
    ora_ts = int(
        istante_riferimento.astimezone(timezone.utc).timestamp()
        if istante_riferimento.tzinfo
        else istante_riferimento.replace(tzinfo=timezone.utc).timestamp()
    )
    if ora_ts > ts_effettivo:
        return False

    # Verifica a tempo costante del MAC
    mac_atteso = calcola_mac(foto_id, canale_norm, ts_effettivo)
    return hmac.compare_digest(mac_atteso, mac_fornito)


def genera_url_pubblico(
    foto_id: int,
    canale: str = "instagram",
    durata_secondi: int = DURATA_PREDEFINITA_SECONDI,
    url_base: str | None = None,
    ora: datetime | None = None,
) -> str:
    """Costruisce l'URL pubblico firmato per il canale (Instagram, spec R-42, CA-81).

    Args:
        foto_id: identificativo numerico della foto.
        canale: canale di destinazione ('instagram' o 'facebook').
        durata_secondi: validità del link in secondi dalla data di generazione.
        url_base: prefisso dell'URL (se omesso legge FOTO_URL_PUBBLICO o lascia relativo).
        ora: istante di riferimento (default: adesso()).

    Returns:
        Stringa URL con query param 'canale' e 'firma'.
    """
    if foto_id <= 0:
        raise DatiNonValidi("ID foto non valido.")

    canale_norm = canale.strip().lower()
    if canale_norm not in PROPORZIONI_CANALE:
        raise DatiNonValidi(
            f"Canale '{canale}' non valido. Canali ammessi: {', '.join(PROPORZIONI_CANALE.keys())}."
        )

    istante = ora if ora is not None else adesso()
    istante_utc = (
        istante.astimezone(timezone.utc)
        if istante.tzinfo
        else istante.replace(tzinfo=timezone.utc)
    )
    scadenza_ts = int(istante_utc.timestamp()) + max(1, durata_secondi)
    firma = componi_firma(foto_id, canale_norm, scadenza_ts)

    base = (
        url_base if url_base is not None else os.getenv("FOTO_URL_PUBBLICO", "").strip()
    )
    base_pulita = base.rstrip("/") if base else ""

    params = {"canale": canale_norm, "firma": firma}
    query_string = urlencode(params)
    return f"{base_pulita}/api/foto/{foto_id}/pubblica?{query_string}"
