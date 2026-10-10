"""L'ora corrente: si inietta (Depends nei router, parametro nei service) e nei test si sostituisce."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.config import leggi_impostazioni

ROMA = ZoneInfo("Europe/Rome")


def adesso() -> datetime:
    """Ora in UTC, spostata in avanti di `OROLOGIO_GIORNI_AVANTI` giorni (prove a mano)."""
    avanti = timedelta(days=leggi_impostazioni().orologio_giorni_avanti)
    return datetime.now(timezone.utc) + avanti
