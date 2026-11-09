"""La diagnosi: l'AI dice che c'è un difetto, la misura lo conferma (ADR-124, RT-24).

``diagnosi(ai, locale)`` è una funzione pura (L2, nota 7.4 e 10.7): prende ciò che l'AI ha
scritto nel suo ``ritocco`` (note, centro, zone, superficie piana, volti) e ciò che il
programma ha misurato (``locale``: misure, fasce, candidati) e dice che cosa si può
correggere. Una correzione di luce o di geometria entra **solo** se le due chiavi girano:
una sola non basta, e il caso si scrive in ``scarti`` (serve a tarare le soglie, RT-34).
La dose non si decide qui: la dà la misura, al momento di eseguire, fino al tetto della
variante. La privacy, al contrario, si propone anche con una sola chiave: nel dubbio decide
l'operatore.

Entrambi gli argomenti possono mancare: senza ``ai`` nessuna correzione (tutte vogliono la
nota dell'AI); senza ``locale`` nessuna correzione (tutte vogliono la misura) e nessun
volto candidato. Nessuna eccezione per risposte o misure strane.
"""

from __future__ import annotations

from typing import Any, Final

from . import ritocco_catalogo as catalogo

_AVVISI_DELLE_NOTE: Final[dict[str, str]] = {
    "riflessi_bordi": "riflessi_ai_bordi",
    "riflessi_soggetto": "riflessi_sul_soggetto",
    "mossa_lieve": "foto_mossa_lieve",
    "mossa_forte": "foto_mossa_forte",
    "foto_di_foto": "foto_di_foto",
    "screenshot": "screenshot",
    "grafica": "grafica",
    "marchi": "marchi_di_altre_aziende",
}
_RUOLI_PRIVATI: Final[tuple[str, ...]] = ("nome", "indirizzo", "targa", "dati")
_SOVRAPPOSIZIONE_VOLTO: Final[float] = 0.3


def _numero(valore: Any) -> float | None:
    if isinstance(valore, bool) or not isinstance(valore, (int, float)):
        return None
    return float(valore)


def _box_centesimi(box: Any) -> list[int] | None:
    """Un riquadro 0–1 ``{x, y, larghezza, altezza}`` come ``[x, y, l, a]`` in centesimi, dentro la foto."""
    if not isinstance(box, dict):
        return None
    try:
        x, y, w, h = (_numero(box[k]) for k in ("x", "y", "larghezza", "altezza"))
    except KeyError:
        return None
    if None in (x, y, w, h):
        return None
    x0, y0 = max(0, round(x * 100)), max(0, round(y * 100))
    x1, y1 = min(100, round((x + w) * 100)), min(100, round((y + h) * 100))
    if x1 - x0 < 1 or y1 - y0 < 1:
        return None
    return [x0, y0, x1 - x0, y1 - y0]


def _iou(a: list[int], b: list[int]) -> float:
    larghezza = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    altezza = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    if larghezza <= 0 or altezza <= 0:
        return 0.0
    comune = larghezza * altezza
    return comune / (a[2] * a[3] + b[2] * b[3] - comune)


def _zone_valide(ai: dict[str, Any]) -> list[dict[str, Any]]:
    zone = ai.get("zone")
    if not isinstance(zone, list):
        return []
    return [
        z
        for z in zone
        if isinstance(z, dict)
        and z.get("ruolo") in catalogo.RUOLI_ZONA
        and isinstance(z.get("b"), list)
        and len(z["b"]) == 4
    ]


def _privacy(ai: dict[str, Any], locale: dict[str, Any]) -> list[dict[str, Any]]:
    """Le zone da proporre: volti candidati (tranne staff e non volti) e ciò che l'AI ha segnato in più."""
    eccezioni: dict[str, str] = {}
    for voce in ai.get("volti") or []:
        if isinstance(voce, str) and len(voce.split()) == 2:
            codice, ruolo = voce.split()
            eccezioni[codice] = ruolo
    zone: list[dict[str, Any]] = []
    candidati = ((locale.get("candidati") or {}).get("volti")) or []
    for candidato in candidati:
        codice = candidato.get("id") if isinstance(candidato, dict) else None
        b = (
            _box_centesimi(candidato.get("box"))
            if isinstance(candidato, dict)
            else None
        )
        if codice is None or b is None:
            continue
        ruolo = eccezioni.get(codice, "cliente")
        if ruolo in ("staff", "no"):
            continue
        zone.append({"origine": codice, "ruolo": ruolo, "b": b})
    for zona in _zone_valide(ai):
        if zona["ruolo"] == "volto":
            # un volto che l'AI segna e che è già un candidato V non si ripete
            if any(_iou(zona["b"], z["b"]) > _SOVRAPPOSIZIONE_VOLTO for z in zone):
                continue
            zone.append({"origine": "ai", "ruolo": "volto", "b": list(zona["b"])})
        elif zona["ruolo"] in _RUOLI_PRIVATI:
            zone.append({"origine": "ai", "ruolo": zona["ruolo"], "b": list(zona["b"])})
    for numero, zona in enumerate(zone, start=1):
        zona["id"] = f"z{numero}"
    return [{"id": z["id"], **{k: v for k, v in z.items() if k != "id"}} for z in zone]


def diagnosi(
    ai: dict[str, Any] | None, locale: dict[str, Any] | None
) -> dict[str, Any]:
    """La diagnosi verificata di una foto (vedi il modulo)."""
    ai = ai if isinstance(ai, dict) else {}
    locale = locale if isinstance(locale, dict) else {}
    note = [
        n for n in ai.get("note") or [] if isinstance(n, str) and n in catalogo.NOTE
    ]
    misure = locale.get("misure") if isinstance(locale.get("misure"), dict) else {}
    fasce = locale.get("fasce") if isinstance(locale.get("fasce"), dict) else {}
    exif = locale.get("exif") if isinstance(locale.get("exif"), dict) else {}
    ha_misure = bool(misure)

    scarti: list[dict[str, str]] = []
    avvisi: list[str] = []

    def scarta(correzione: str, motivo: str) -> None:
        scarti.append({"correzione": correzione, "motivo": motivo})

    def chiavi(correzione: str, ai_dice: bool, misura_dice: bool) -> bool:
        """Entrambe: sì. Una sola: scarto con il perché. Nessuna: niente da dire."""
        if ai_dice and misura_dice:
            return True
        if ai_dice:
            scarta(correzione, "ai_si_misura_no" if ha_misure else "senza_misure")
        elif misura_dice:
            scarta(correzione, "misura_si_ai_no")
        return False

    for nota in note:
        if nota in _AVVISI_DELLE_NOTE:
            avvisi.append(_AVVISI_DELLE_NOTE[nota])
    if fasce.get("compressione") == "forte":
        avvisi.append("compressione_forte")

    solo_originale = any(n in catalogo.NOTE_SOLO_ORIGINALE for n in note)
    ruota = next((int(n.split("_")[1]) for n in note if n.startswith("ruota_")), 0)
    non_tagliare = "non_tagliare" in note
    centro = ai.get("centro")
    risultato: dict[str, Any] = {
        "versione": catalogo.VERSIONE_DIAGNOSI,
        "solo_originale": solo_originale,
        "ruota": ruota,
        "avvicina": False,
        "ambiente": False,
        "non_tagliare": non_tagliare,
        "centro": list(centro)
        if isinstance(centro, list) and len(centro) == 2
        else None,
        "tieni": [list(z["b"]) for z in _zone_valide(ai) if z["ruolo"] == "tieni"],
        "togli": [list(z["b"]) for z in _zone_valide(ai) if z["ruolo"] == "togli"],
        "neutro": next(
            (list(z["b"]) for z in _zone_valide(ai) if z["ruolo"] == "neutro"), None
        ),
        "raddrizza": None,
        "luce": {"esposizione": None, "bianco": None, "ombre": False, "flash": False},
        "nitidezza": False,
        "privacy": _privacy(ai, locale),
        "avvisi": avvisi,
        "scarti": scarti,
    }
    if solo_originale:
        if any(
            n in note for n in ("scura", "chiara", "storta", "lontana", "decentrata")
        ):
            scarta("correzioni", "solo_originale")
        return risultato

    # --- Inquadratura -----------------------------------------------------------
    if non_tagliare:
        risultato["togli"] = []  # nessun taglio oltre quello del rapporto
    else:
        ambiente = "ambiente" in note
        risultato["ambiente"] = ambiente
        risultato["avvicina"] = ambiente or "lontana" in note or "decentrata" in note

    # --- Geometria: prospettiva prima della rotazione fine -----------------------
    codice = ai.get("piana")
    quadro = None
    if codice:
        for candidato in (locale.get("candidati") or {}).get("quadrilateri") or []:
            if isinstance(candidato, dict) and candidato.get("id") == codice:
                quadro = candidato
        if (
            quadro is None
            or not isinstance(quadro.get("angoli"), list)
            or len(quadro["angoli"]) != 4
        ):
            scarta("prospettiva", "piana_senza_candidato")
            quadro = None
    if quadro is not None:
        risultato["raddrizza"] = {
            "tipo": "prospettiva",
            "codice": codice,
            "angoli": [[float(x), float(y)] for x, y in quadro["angoli"]],
        }
    angolo = _numero(misure.get("angolo_linee"))
    in_misura = angolo is not None and (
        catalogo.ROTAZIONE_MIN_GRADI
        <= abs(angolo)
        <= catalogo.DIAGNOSI_ROTAZIONE_MAX_GRADI
    )
    if chiavi("rotazione", "storta" in note, in_misura) and quadro is None:
        risultato["raddrizza"] = {"tipo": "rotazione", "gradi": float(angolo)}
    elif "storta" in note and in_misura and quadro is not None:
        scarta("rotazione", "assorbita_dalla_prospettiva")

    # --- Luce ---------------------------------------------------------------------
    luce = risultato["luce"]
    esposizione = fasce.get("esposizione")
    if chiavi("esposizione_su", "scura" in note, esposizione == "scura"):
        luce["esposizione"] = "su"
    elif chiavi(
        "esposizione_giu",
        "chiara" in note,
        esposizione == "chiara"
        and fasce.get("luci_bruciate", "nessuna") in catalogo.DIAGNOSI_LUCI_BRUCIATE_OK,
    ):
        luce["esposizione"] = "giu"
    dominanti = [n for n in note if n in catalogo.NOTE_DOMINANTE]
    misurata = fasce.get("dominante")
    if dominanti:
        if misurata == dominanti[0]:
            luce["bianco"] = {
                "dominante": dominanti[0],
                "neutro": risultato["neutro"],
                "senza_neutro": risultato["neutro"] is None,
            }
        else:
            scarta("bianco", "ai_si_misura_no" if ha_misure else "senza_misure")
    elif misurata in catalogo.NOTE_DOMINANTE:
        scarta("bianco", "misura_si_ai_no")
    if chiavi(
        "ombre",
        "controluce" in note,
        fasce.get("ombre_chiuse") in ("poche", "molte"),
    ):
        luce["ombre"] = True
    caduta = _numero(misure.get("caduta_bordi"))
    if chiavi(
        "flash",
        "flash" in note,
        caduta is not None and caduta >= catalogo.DIAGNOSI_FLASH_CADUTA_MIN,
    ):
        luce["flash"] = True

    # --- Nitidezza finale: foto molle, non mossa, non troppo compressa, senza zoom ----
    zoom = _numero(exif.get("zoom_digitale"))
    risultato["nitidezza"] = bool(
        fasce.get("nitidezza") == "bassa"
        and "mossa_forte" not in note
        and fasce.get("compressione") != "forte"
        and (zoom is None or zoom <= catalogo.NITIDEZZA_ZOOM_MAX)
    )
    return risultato
