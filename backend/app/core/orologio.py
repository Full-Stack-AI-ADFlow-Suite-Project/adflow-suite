"""L'ora corrente: si inietta (Depends nei router, parametro nei service) e nei test si sostituisce."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROMA = ZoneInfo("Europe/Rome")


def adesso() -> datetime:
    return datetime.now(timezone.utc)
