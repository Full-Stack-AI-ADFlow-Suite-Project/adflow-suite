"""La preparazione dell'analisi di una foto: una decodifica, tutto il resto (ADR-124, RT-19).

Per ogni foto da analizzare si decodifica **una volta sola** (``colore.apri_in_srgb``, con
``draft()`` per i JPEG) e da quella copia di lavoro (~2048 px) si ricavano la copia per
l'AI (1024 px, JPEG q85), le misure, le fasce e i candidati. Il risultato è:

- ``immagine``: il JPEG per l'AI (``None`` se la foto non si legge: l'adattatore la
  rifiuta come richiesta su quella foto);
- ``contesto``: una riga di testo per l'AI con le sole fasce non normali e i candidati
  (vuota per una foto pulita);
- ``locale``: ``foto.analisi_ai["locale"]`` (nota 10.3), da salvare con l'analisi.

Un errore nelle misure o nei candidati non ferma niente: la foto va all'AI senza
contesto e senza ``locale`` (e poi con la sola variante Originale).
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Any, Final

from PIL import Image

from app.core.config import leggi_impostazioni

from . import preanalisi
from . import ritocco_catalogo as catalogo
from .colore import apri_in_srgb

_log = logging.getLogger(__name__)

# La copia che si manda all'AI: sRGB, al massimo 1024 px sul lato lungo, JPEG q85.
LATO_COPIA_AI: Final[int] = 1024
QUALITA_COPIA_AI: Final[int] = 85
# La copia di lavoro per misure e candidati: ~2048 px (con draft() può essere un po' più grande).
LATO_LAVORO: Final[int] = 2048

# Come le fasce non normali si dicono all'AI: poche parole, perché ogni foto ha la sua riga.
_PAROLE: Final[dict[str, dict[str, str]]] = {
    "nitidezza": {"bassa": "nitidezza bassa"},
    "esposizione": {"scura": "scura", "chiara": "chiara"},
    "luci_bruciate": {"poche": "poche luci bruciate", "molte": "luci bruciate"},
    "ombre_chiuse": {"poche": "poche ombre chiuse", "molte": "ombre chiuse"},
    "compressione": {"forte": "compressione forte", "lieve": "compressione lieve"},
}


def contesto_di(fasce: dict[str, str], locale: dict[str, Any]) -> str:
    """Il contesto per l'AI: ``"scura, nitidezza bassa, flash; candidati V1 V2"``. Vuoto se non c'è niente da dire."""
    parti = []
    for misura, fascia in fasce.items():
        if misura == "dominante":
            parti.append(f"dominante {fascia}")
        else:
            parti.append(_PAROLE[misura][fascia])
    if (locale.get("exif") or {}).get("flash"):
        parti.append("flash")
    testo = ", ".join(parti)
    codici = [c["id"] for c in locale["candidati"]["volti"]] + [
        c["id"] for c in locale["candidati"]["quadrilateri"]
    ]
    if codici:
        testo += ("; " if testo else "") + "candidati " + " ".join(codici)
    return testo


def _arrotonda(valore: Any) -> Any:
    if isinstance(valore, float):
        return round(valore, 4)
    if isinstance(valore, dict):
        return {k: _arrotonda(v) for k, v in valore.items()}
    if isinstance(valore, (list, tuple)):
        return [_arrotonda(v) for v in valore]
    return valore


def analisi_locale(
    originale: bytes, copia: Image.Image, con_candidati: bool = True
) -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    """(locale, fasce, candidati) di una foto: misure, fasce e candidati sulla copia di lavoro.

    Senza ``con_candidati`` (il ricalcolo di una foto già analizzata, RT-27) i candidati sono
    vuoti: nessuna risposta dell'AI li cita, quindi un ``V1`` nuovo non avrebbe senso.
    """
    misure = preanalisi.misura(copia, originale)
    fasce = preanalisi.fasce(misure)
    trovati = (
        preanalisi.candidati(copia)
        if con_candidati
        else {"volti": [], "quadrilateri": []}
    )
    esif = misure.pop("exif")
    locale = _arrotonda(
        {
            "versione": catalogo.VERSIONE_LOCALE,
            **preanalisi.formato_e_colore(originale),
            "exif": esif,
            "misure": misure,
            "fasce": fasce,
            "candidati": trovati,
        }
    )
    return locale, fasce, trovati


def prepara_foto(originale: bytes, foto_id: int) -> dict[str, Any]:
    """L'immagine per l'AI, il contesto e il ``locale`` di una foto (vedi il modulo).

    Raises:
        DatiNonValidi: il file non si decodifica (come ``colore.apri_in_srgb``).
    """
    copia = apri_in_srgb(originale, lato_max=LATO_LAVORO)  # l'unica decodifica
    per_ai = copia.copy()
    per_ai.thumbnail((LATO_COPIA_AI, LATO_COPIA_AI))
    risultato: dict[str, Any] = {"immagine": None, "contesto": "", "locale": None}
    try:
        locale, fasce, trovati = analisi_locale(originale, copia)
        risultato["locale"] = locale
        risultato["contesto"] = contesto_di(fasce, locale)
        if leggi_impostazioni().ritocco_segni:
            per_ai = preanalisi.disegna_segni(per_ai, trovati)
    except (
        Exception
    ):  # noqa: BLE001 - L1 non ferma la generazione: la foto va senza contesto
        _log.warning(
            "Pre-analisi locale non riuscita per la foto %s", foto_id, exc_info=True
        )
    uscita = BytesIO()
    per_ai.save(uscita, "JPEG", quality=QUALITA_COPIA_AI)
    risultato["immagine"] = uscita.getvalue()
    return risultato
