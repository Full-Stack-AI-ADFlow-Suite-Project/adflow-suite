"""Dalla risposta strutturata dell'AI all'analisi che il resto dell'app legge (ADR-124, RT-23).

Lo stesso passaggio per l'adattatore vero e per il finto: il finto scrive una risposta nel
formato compatto, la fa passare per lo stesso schema (``schemi.RispostaAnalisi``, con i suoi
validatori morbidi) e per questa conversione. Così un test col finto prova anche la
traduzione, non solo il codice che sta a valle.
"""

import re
from collections.abc import Sequence
from typing import Any

from .base import ErroreAI, FotoAI
from .schemi import AnalisiFoto, RispostaAnalisi, riquadro_da_centesimi


def persone_riconoscibili(ritocco: Any, contesto: str) -> bool:
    """Derivato (nota 12.2): c'è un volto riconoscibile se una zona lo dice, se l'AI cita un volto
    dello staff o minorenne, o se un candidato ``V`` del contesto non è stato escluso con ``no``.
    """
    if ritocco is not None:
        if any(zona.ruolo == "volto" for zona in ritocco.zone):
            return True
        if any(voce.endswith((" staff", " minore")) for voce in ritocco.volti):
            return True
    candidati = set(re.findall(r"\bV\d+\b", contesto))
    esclusi = {
        voce.split()[0]
        for voce in (ritocco.volti if ritocco else [])
        if voce.endswith(" no")
    }
    return bool(candidati - esclusi)


def spezza_i_cicli(analisi: dict[int, dict[str, Any]]) -> None:
    """Se due scatti (o più) si dicono doppioni a vicenda, la migliore resta libera.

    Senza, tutte le foto del ciclo uscirebbero dalle disponibili (R-05).
    """
    for inizio in list(analisi):
        visti = [inizio]
        corrente = analisi[inizio]["simile_a"]
        while corrente is not None and corrente not in visti:
            visti.append(corrente)
            corrente = analisi[corrente]["simile_a"]
        if corrente != inizio:
            continue
        migliore = max(visti, key=lambda uno: (analisi[uno]["punteggio"], -uno))
        analisi[migliore]["simile_a"] = None


def analisi_da_risposta(
    risposta: RispostaAnalisi, foto: Sequence[FotoAI]
) -> dict[int, dict[str, Any]]:
    """L'analisi di ogni foto del gruppo, nel formato di ``foto.analisi_ai`` più il ``ritocco`` per L2.

    Raises:
        ErroreAI: ``risposta`` se la risposta non riguarda tutte le foto del gruppo (R-35).
    """
    ids = [una.id for una in foto]
    per_id: dict[int, AnalisiFoto] = {voce.foto_id: voce for voce in risposta.foto}
    if len(risposta.foto) != len(ids) or set(per_id) != set(ids):
        raise ErroreAI(
            "risposta", "L'analisi dell'AI non riguarda tutte le foto del gruppo."
        )
    contesti = {una.id: una.contesto for una in foto}
    analisi: dict[int, dict[str, Any]] = {}
    for uno in ids:
        voce = per_id[uno]
        simile = voce.simile_a if voce.simile_a in per_id else None
        analisi[uno] = {
            "idonea": voce.idonea,
            "simile_a": simile if simile != uno else None,
            "tipo": voce.tipo,
            "punteggio": voce.punteggio,
            "motivo": voce.motivo if not voce.idonea else None,
            "soggetto": voce.soggetto,
            "descrizione": voce.descrizione,
            # Il formato di oggi, 0–1: chi legge `analisi_ai` non cambia (RT-20).
            "soggetto_box": riquadro_da_centesimi(voce.soggetto_box),
            "persone_riconoscibili": persone_riconoscibili(
                voce.ritocco, contesti.get(uno, "")
            ),
            "marchi_visibili": bool(voce.ritocco and "marchi" in voce.ritocco.note),
            # Per L2 (diagnosi) così com'è, già validato in modo morbido.
            "ritocco": voce.ritocco.model_dump() if voce.ritocco else None,
        }
        if not voce.idonea and not voce.motivo:
            analisi[uno]["motivo"] = "La foto non è adatta."
    spezza_i_cicli(analisi)
    return analisi
