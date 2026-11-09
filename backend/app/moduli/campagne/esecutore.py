"""L'esecutore: un comando, dieci passi fissi, un JPEG (ADR-124, RT-04).

Un solo esecutore per l'anteprima e per la pubblicazione. L'ordine dei passi lo
decide il codice (nota 7.5), non l'AI e non l'operatore:

| # | Passo        | Stato |
|---|--------------|-------|
| 1 | decodifica   | `colore.apri_in_srgb`: unico decoder, limiti di oggi |
| 2 | srgb         | EXIF, poi conversione in sRGB (stessa funzione) |
| 3 | ruota        | rotazione di 90° (`geometria.ruota_90`) |
| 4 | privacy      | RT-18 (vuoto: nessuna zona sfocata) |
| 5 | raddrizza    | rotazione fine o prospettiva (`geometria`); un controllo che fallisce salta il passo, non il comando |
| 6 | finestra     | le regole di R-42 di oggi (`sistemazione_foto`); RT-16 aggiunge la finestra esplicita |
| 7 | lato_corto   | lato corto 1080 |
| 8 | luce         | RT-17 (vuoto) |
| 9 | nitidezza    | RT-17 (vuoto) |
| 10| codifica     | JPEG q90, profilo sRGB, nessun metadato |

I passi vuoti non fanno nulla: si riempiono nei task indicati, senza cambiare
l'ordine né la firma. Un comando è dato puro (nessun file, nessun database):
`comando_originale` ricostruisce quello di oggi, cioè le regole di R-42 senza
l'autocontrasto per canale, che non c'è più.
"""

from __future__ import annotations

import io
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Final

from PIL import Image

from app.core.errori import DatiNonValidi

from . import geometria
from . import ritocco_catalogo as catalogo
from . import sistemazione_foto as regole
from .colore import apri_in_srgb, profilo_srgb_bytes

# Cambia quando cambia l'uscita dell'esecutore: entra nella chiave dei render (RT-06).
VERSIONE_ESECUTORE: Final[str] = "ritocco-1"

# L'ordine fisso (nota 7.5). `esegui` lo rispetta e, se glielo si chiede, lo racconta.
PASSI: Final[tuple[str, ...]] = (
    "decodifica",
    "srgb",
    "ruota",
    "privacy",
    "raddrizza",
    "finestra",
    "lato_corto",
    "luce",
    "nitidezza",
    "codifica",
)

QUALITA_JPEG_USCITA: Final[int] = 90
_ROTAZIONI_AMMESSE: Final[tuple[int, ...]] = (0, 90, 180, 270)


@dataclass(frozen=True)
class RegoleR42:
    """La finestra come la decidono le regole di R-42 (rapporto, soggetto, centro, bordi sfocati).

    ``proporzione`` è la proporzione forzata a mano ('1:1' o '4:5', decisione D3 del
    piano: resta com'è); ``soggetto_box`` il riquadro normalizzato dell'AI.
    """

    canale: str = "instagram"
    proporzione: str | None = None
    soggetto_box: dict[str, float] | None = None


@dataclass(frozen=True)
class Comando:
    """Che cosa fare a una foto. Dato puro: lo stesso comando dà sempre gli stessi pixel.

    ``finestra`` vuota vuol dire nessun taglio (solo il lato corto a 1080).
    ``ruota`` è in gradi, in senso orario (0, 90, 180, 270): la correzione di una
    foto girata. ``raddrizza`` è ``{"tipo": "rotazione", "gradi": g}`` (``g`` come
    lo misura ``preanalisi``) oppure ``{"tipo": "prospettiva", "angoli": [[x, y]×4]}``
    (alto-sx, alto-dx, basso-dx, basso-sx, normalizzati nel riferimento dopo EXIF e
    sRGB), con ``max`` facoltativo: i gradi o la deformazione oltre cui il passo si
    salta (senza, i tetti della variante Standard). Gli altri campi sono per i task
    successivi e oggi non hanno effetto.
    """

    versione: str = VERSIONE_ESECUTORE
    ruota: int = 0
    raddrizza: dict[str, Any] | None = None
    finestra: RegoleR42 | None = None
    barre: str | None = None
    luce: dict[str, Any] | None = None
    nitidezza: bool = False

    def __post_init__(self) -> None:
        if self.ruota not in _ROTAZIONI_AMMESSE:
            raise DatiNonValidi(
                f"Rotazione {self.ruota}° non ammessa: valori validi 0, 90, 180, 270."
            )


def comando_originale(
    foto: Any | None = None,
    *,
    canale: str = "instagram",
    proporzione: str | None = None,
    soggetto_box: dict[str, float] | None = None,
) -> Comando:
    """Il comando della variante Originale: le regole di R-42 di oggi, senza autocontrasto.

    Il riquadro del soggetto si prende da ``soggetto_box`` o, se manca, da
    ``foto.analisi_ai`` (una foto già analizzata dall'AI).
    """
    if soggetto_box is None and foto is not None:
        analisi = getattr(foto, "analisi_ai", None)
        if isinstance(analisi, dict):
            soggetto_box = analisi.get("soggetto_box")
    return Comando(
        finestra=RegoleR42(
            canale=canale, proporzione=proporzione, soggetto_box=soggetto_box
        )
    )


# --- I passi ---------------------------------------------------------------------


@dataclass
class _Contesto:
    """Quello che i passi si passano: dove sono finiti i punti del riferimento di partenza."""

    mappa: geometria.Mappa
    zone: Sequence[Any] = ()
    avvisi: list[str] = field(default_factory=list)


_Passo = Callable[[Image.Image, Comando, "str | None", _Contesto], Image.Image]


def _passo_ruota(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    img, ctx.mappa = geometria.ruota_90(img, comando.ruota, ctx.mappa)
    return img


def _passo_privacy(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    return img  # RT-18 (le zone arrivano a `esegui`)


def _passo_raddrizza(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    """Rotazione fine o prospettiva; se un controllo non passa il passo si salta."""
    r = comando.raddrizza
    if not r:
        return img
    tipo = r.get("tipo")
    if tipo == "rotazione":
        gradi = r.get("gradi")
        massimo = r.get("max", catalogo.STANDARD.rotazione_max_gradi)
        if not isinstance(gradi, (int, float)) or not (
            catalogo.ROTAZIONE_MIN_GRADI <= abs(gradi) <= massimo
        ):
            ctx.avvisi.append("raddrizza_saltato")
            return img
        img, ctx.mappa = geometria.raddrizza_rotazione(img, float(gradi), ctx.mappa)
        return img
    if tipo == "prospettiva":
        esito = geometria.raddrizza_prospettiva(
            img,
            r.get("angoli") or [],
            ctx.mappa,
            r.get("max", catalogo.STANDARD.prospettiva_deformazione_max),
        )
        if esito is None:
            ctx.avvisi.append("raddrizza_saltato")
            return img
        img, ctx.mappa = esito
        return img
    ctx.avvisi.append("raddrizza_saltato")
    return img


def _passo_finestra(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    """Le regole di R-42: rapporto più vicino nell'intervallo, soggetto, centro, bordi sfocati."""
    r42 = comando.finestra
    if r42 is None or canale is None:
        return img
    target = regole._ratio_target(
        ratio_corrente=regole._calcola_ratio(img.width, img.height),
        proporzioni_ammesse=regole.PROPORZIONI_CANALE[canale],
        proporzione_richiesta=r42.proporzione,
    )
    if target is None:
        return img
    # Il riquadro del soggetto è nel riferimento di partenza: lo si porta sulla foto di adesso.
    soggetto = ctx.mappa.box_norm(r42.soggetto_box) if r42.soggetto_box else None
    return regole._adatta_alle_proporzioni(img, target, soggetto_box=soggetto)


def _passo_lato_corto(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    return regole._ridimensiona_lato_corto(img, regole.LATO_CORTO_TARGET)


def _passo_luce(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    return img  # RT-17


def _passo_nitidezza(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    return img  # RT-17


_DOPO_LA_DECODIFICA: Final[tuple[tuple[str, _Passo], ...]] = (
    ("ruota", _passo_ruota),
    ("privacy", _passo_privacy),
    ("raddrizza", _passo_raddrizza),
    ("finestra", _passo_finestra),
    ("lato_corto", _passo_lato_corto),
    ("luce", _passo_luce),
    ("nitidezza", _passo_nitidezza),
)


def _canale_valido(canale: str) -> str:
    normalizzato = canale.strip().lower()
    if normalizzato not in regole.PROPORZIONI_CANALE:
        raise DatiNonValidi(
            f"Canale '{canale}' non valido. Canali ammessi: "
            f"{', '.join(regole.PROPORZIONI_CANALE.keys())}."
        )
    return normalizzato


def esegui(
    dati: bytes,
    comando: Comando,
    zone_privacy: Sequence[Any] = (),
    *,
    traccia: list[str] | None = None,
    avvisi: list[str] | None = None,
) -> bytes:
    """Applica ``comando`` ai byte di una foto e restituisce il JPEG (sRGB, senza metadati).

    Su una copia in memoria: l'originale non cambia (§1.3). Se ``traccia`` è una
    lista, ci si scrivono i nomi dei passi nell'ordine in cui girano; se ``avvisi``
    è una lista, ci si scrivono i passi saltati per un controllo (``raddrizza_saltato``).

    Raises:
        DatiNonValidi: dati vuoti, file non valido o troppo grande, canale o
            proporzione non ammessi.
    """
    if not dati:
        raise DatiNonValidi("Nessun dato immagine fornito.")
    canale = _canale_valido(comando.finestra.canale) if comando.finestra else None
    passi = traccia if traccia is not None else []

    # 1-2. Decodifica, EXIF e sRGB: una funzione sola per tutte le foto (RT-02).
    # Il limite si legge qui, a ogni chiamata (così i test lo possono abbassare).
    img = apri_in_srgb(dati, max_pixel=regole.MAX_PIXEL_TOTALI)
    passi.extend(("decodifica", "srgb"))
    ctx = _Contesto(geometria.Mappa.identita(*img.size), zone_privacy)

    # 3-9. In ordine fisso; i passi non ancora scritti non fanno nulla.
    for nome, passo in _DOPO_LA_DECODIFICA:
        img = passo(img, comando, canale, ctx)
        passi.append(nome)
    if avvisi is not None:
        avvisi.extend(ctx.avvisi)

    # 10. JPEG pulito: senza EXIF né GPS, con il profilo sRGB incorporato.
    uscita = io.BytesIO()
    img.save(
        uscita,
        format="JPEG",
        quality=QUALITA_JPEG_USCITA,
        optimize=True,
        icc_profile=profilo_srgb_bytes(),
    )
    passi.append("codifica")
    return uscita.getvalue()


def sistema_foto_buffer(
    dati_foto: bytes,
    canale: str = "instagram",
    proporzione: str | None = None,
    soggetto_box: dict[str, float] | None = None,
) -> bytes:
    """Sistemazione locale di una foto secondo R-42 e CA-114: la variante Originale.

    Involucro dell'esecutore (firma invariata da prima di ADR-124): costruisce
    ``comando_originale`` e lo esegue. Rotazione da EXIF, GPS tolto, colore in
    sRGB, rapporto da 4:5 a 1,91:1 con ritaglio sul soggetto, al centro o bordi
    sfocati, lato corto a 1080 px, JPEG. Niente autocontrasto.

    Raises:
        DatiNonValidi: se i byte non sono un'immagine valida o il canale o la
            proporzione non sono ammessi.
    """
    return esegui(
        dati_foto,
        comando_originale(
            canale=canale, proporzione=proporzione, soggetto_box=soggetto_box
        ),
    )
