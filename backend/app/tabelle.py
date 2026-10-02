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
