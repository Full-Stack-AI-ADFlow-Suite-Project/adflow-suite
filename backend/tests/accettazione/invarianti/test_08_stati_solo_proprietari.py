"""§1.8 — Gli stati cambiano solo nel modulo proprietario, con verifica_transizione.

Attacco di §4.3: cercare con `ast` le assegnazioni a `.stato` fuori da
`campagne.service.cambia_stato()`, da `contenuti.service` e dallo stato del
tentativo di pubblicazione (riga interna di `pubblicazione`).
"""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"

# Le sole assegnazioni a `.stato` ammesse (attacco §1.8 di accettazione-post-mvp).
AMMESSI = {
    "moduli/campagne/service.py",  # dentro cambia_stato(), controllato sotto
    "moduli/contenuti/service.py",  # il modulo proprietario dello stato del post
    "moduli/pubblicazione/service.py",  # lo stato del tentativo (in_corso/ok/in errore)
}


def _assegnazioni_a_stato(percorso: Path) -> list[tuple[int, str]]:
    albero = ast.parse(percorso.read_text("utf-8"))
    trovate = []
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.Assign):
            target = nodo.targets[0]
        elif isinstance(nodo, (ast.AnnAssign, ast.AugAssign)):
            target = nodo.target
        else:
            continue
        if isinstance(target, ast.Attribute) and target.attr == "stato":
            trovate.append((nodo.lineno, ast.unparse(target)))
    return trovate


def test_le_assegnazioni_a_stato_sono_solo_nei_moduli_proprietari():
    """Nessun modulo fuori dai proprietari scrive `.stato` a mano (costituzione §1.8)."""
    violazioni = []
    for percorso in sorted(APP.rglob("*.py")):
        relativo = percorso.relative_to(APP).as_posix()
        for riga, espressione in _assegnazioni_a_stato(percorso):
            if relativo not in AMMESSI:
                violazioni.append(f"{relativo}:{riga}: {espressione}")
    assert not violazioni, "assegnazioni a .stato fuori dai moduli proprietari:\n" + (
        "\n".join(violazioni)
    )


def test_lo_stato_della_campagna_cambia_solo_in_cambia_stato():
    """In campagne/service.py `.stato` si tocca solo dentro `cambia_stato()`."""
    percorso = APP / "moduli" / "campagne" / "service.py"
    albero = ast.parse(percorso.read_text("utf-8"))
    nomi = set()
    for nodo in ast.walk(albero):
        if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for figlio in ast.walk(nodo):
            targets = []
            if isinstance(figlio, ast.Assign):
                targets = figlio.targets
            elif isinstance(figlio, (ast.AnnAssign, ast.AugAssign)):
                targets = [figlio.target]
            if any(
                isinstance(target, ast.Attribute) and target.attr == "stato"
                for target in targets
            ):
                nomi.add(nodo.name)
    assert nomi == {"cambia_stato"}, f"`.stato` si assegna anche in {sorted(nomi)}"
