"""Tutte le tabelle: importa i models.py dei moduli così Alembic e i test vedono il modello intero."""

from importlib import import_module
from importlib.util import find_spec

from app.core.db import Base

MODULI = (
    "accesso",
    "notifiche",
    "artigiani",
    "campagne",
    "contenuti",
    "revisione",
    "pubblicazione",
)

for _modulo in MODULI:
    if find_spec(f"app.moduli.{_modulo}.models") is not None:
        import_module(f"app.moduli.{_modulo}.models")

metadata = Base.metadata


def del_modello(nome: str | None, tipo: str, genitori: dict) -> bool:
    """Filtro `include_name` di Alembic: le tabelle della coda non sono del modello."""
    return not (tipo == "table" and (nome or "").startswith("procrastinate_"))
