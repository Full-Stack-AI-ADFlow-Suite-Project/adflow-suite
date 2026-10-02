"""Regole di import di constitution §2: questo test deve restare verde."""

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
ORDINE = (
    "accesso",
    "notifiche",
    "artigiani",
    "campagne",
    "contenuti",
    "revisione",
    "pubblicazione",
)
IMPORTABILI = {"service", "schemas"}


def _importati(nome: str, sorgente: str, pacchetto: bool) -> set[str]:
    """Nomi completi importati da un file, con gli import relativi risolti."""
    base = nome.split(".") if pacchetto else nome.split(".")[:-1]
    trovati: set[str] = set()
    for nodo in ast.walk(ast.parse(sorgente)):
        if isinstance(nodo, ast.Import):
            trovati.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            parti = base[: len(base) - (nodo.level - 1)] if nodo.level else []
            if nodo.module:
                parti = parti + nodo.module.split(".")
            trovati.update(".".join(parti + [alias.name]) for alias in nodo.names)
    return trovati


def violazioni(nome: str, sorgente: str, pacchetto: bool = False) -> list[str]:
    """Import vietati nel file `nome` (es. app.moduli.campagne.service)."""
    origine = nome.split(".")
    zona = origine[1] if len(origine) > 1 else ""
    proprio = origine[2] if zona == "moduli" and len(origine) > 2 else None
    if zona not in ("moduli", "core", "adapters"):
        return []  # composizione: può conoscere tutti i moduli

    errori = []
    for importato in sorted(_importati(nome, sorgente, pacchetto)):
        parti = importato.split(".")
        if parti[:2] != ["app", "moduli"] or len(parti) < 3:
            continue
        altro = parti[2]
        if altro not in ORDINE or altro == proprio:
            continue
        if proprio is None:
            errori.append(f"{nome}: {zona} non importa dai moduli ({importato})")
        elif len(parti) < 4 or parti[3] not in IMPORTABILI:
            errori.append(
                f"{nome}: di {altro} si importa solo service o schemas ({importato})"
            )
        elif ORDINE.index(altro) > ORDINE.index(proprio):
            errori.append(f"{nome}: {altro} viene dopo {proprio} ({importato})")
    return errori


def test_confini_del_codice() -> None:
    errori = []
    for file in sorted(APP.rglob("*.py")):
        relativo = file.relative_to(APP.parent).with_suffix("")
        pacchetto = relativo.name == "__init__"
        parti = relativo.parts[:-1] if pacchetto else relativo.parts
        errori += violazioni(".".join(parti), file.read_text("utf-8"), pacchetto)
    assert errori == []


def test_i_moduli_sono_quelli_previsti() -> None:
    presenti = {p.name for p in (APP / "moduli").iterdir() if p.is_dir()}
    assert presenti - {"__pycache__"} == set(ORDINE)


@pytest.mark.parametrize(
    ("nome", "sorgente"),
    [
        ("app.moduli.campagne.service", "from app.moduli.accesso import service"),
        ("app.moduli.campagne.service", "from app.moduli.accesso.schemas import X"),
        ("app.moduli.campagne.service", "from . import models"),
        ("app.moduli.campagne.router", "from .service import crea"),
        ("app.moduli.campagne.service", "from app.core.db import Base"),
        ("app.main", "from app.moduli.pubblicazione import router"),
        ("app.tabelle", "import app.moduli.campagne.models"),
    ],
)
def test_import_ammessi(nome: str, sorgente: str) -> None:
    assert violazioni(nome, sorgente) == []


@pytest.mark.parametrize(
    ("nome", "sorgente"),
    [
        ("app.moduli.campagne.service", "from app.moduli.accesso import models"),
        ("app.moduli.campagne.service", "from app.moduli.accesso.models import Utente"),
        ("app.moduli.campagne.service", "import app.moduli.accesso.router"),
        ("app.moduli.campagne.service", "from app.moduli.accesso import jobs"),
        ("app.moduli.campagne.service", "from app.moduli import accesso"),
        ("app.moduli.campagne.service", "from ..accesso import models"),
        ("app.moduli.campagne.service", "from app.moduli.contenuti import service"),
        ("app.moduli.campagne.router", "from ..contenuti.service import genera"),
        ("app.core.db", "from app.moduli.accesso import service"),
        ("app.adapters.ai.finto", "from app.moduli.contenuti import service"),
    ],
)
def test_import_vietati(nome: str, sorgente: str) -> None:
    assert len(violazioni(nome, sorgente)) == 1
