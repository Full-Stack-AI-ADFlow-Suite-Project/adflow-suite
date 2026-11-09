"""L'esecutore: un comando, dieci passi fissi, un JPEG (ADR-124, RT-04).

Un solo esecutore per l'anteprima e per la pubblicazione. L'ordine dei passi lo
decide il codice (nota 7.5), non l'AI e non l'operatore:

| # | Passo        | Stato |
|---|--------------|-------|
| 1 | decodifica   | `colore.apri_in_srgb`: unico decoder, limiti di oggi |
| 2 | srgb         | EXIF, poi conversione in sRGB (stessa funzione) |
| 3 | ruota        | rotazione di 90° (`geometria.ruota_90`) |
| 4 | privacy      | sfocatura forte delle zone attive (`privacy.oscura_zone`) |
| 5 | raddrizza    | rotazione fine o prospettiva (`geometria`); un controllo che fallisce salta il passo, non il comando |
| 6 | finestra     | la `Finestra` esplicita del comando (`finestra.calcola_finestra`), con le barre se serve; o le regole di R-42 di oggi (variante Originale) |
| 7 | lato_corto   | lato corto 1080 |
| 8 | luce         | esposizione, bianco, ombre, flash (`luce.correggi_luce`), misurati nella regione del soggetto |
| 9 | nitidezza    | `UnsharpMask` (`luce.nitidezza`), spenta con compressione forte o zoom digitale |
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
from . import luce as luce_foto
from . import privacy
from . import ritocco_catalogo as catalogo
from . import sistemazione_foto as regole
from .colore import apri_in_srgb, profilo_srgb_bytes
from .finestra import Finestra
from .preanalisi import fatti_del_file

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

    ``finestra`` è ``RegoleR42`` (le regole di R-42 di oggi: la variante Originale), una
    ``Finestra`` esplicita già calcolata (``finestra.calcola_finestra``, nella foto dopo
    i passi geometrici) o vuota, e allora nessun taglio (solo il lato corto a 1080).
    ``barre`` (``"sfocate"`` o ``"neutre"``) dice come riempire se la finestra da sola
    esce dall'intervallo dei rapporti.
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
    finestra: RegoleR42 | Finestra | None = None
    barre: str | None = None
    luce: dict[str, Any] | None = None
    nitidezza: bool = False
    nitidezza_dose: float = catalogo.STANDARD.nitidezza_dose

    def a_dict(self) -> dict[str, Any]:
        """Il comando come dato JSON (si salva in ``foto.analisi_ai["ritocco"]``)."""
        if isinstance(self.finestra, Finestra):
            finestra: dict[str, Any] | None = {
                "b": list(self.finestra.b),
                "rapporto": self.finestra.rapporto,
            }
        elif isinstance(self.finestra, RegoleR42):
            finestra = {
                "regole": "r42",
                "canale": self.finestra.canale,
                "proporzione": self.finestra.proporzione,
                "soggetto_box": self.finestra.soggetto_box,
            }
        else:
            finestra = None
        return {
            "versione": self.versione,
            "ruota": self.ruota,
            "raddrizza": self.raddrizza,
            "finestra": finestra,
            "barre": self.barre,
            "luce": self.luce,
            "nitidezza": self.nitidezza,
            "nitidezza_dose": self.nitidezza_dose,
        }

    @classmethod
    def da_dict(cls, dati: dict[str, Any]) -> "Comando":
        """Il comando salvato con ``a_dict``.

        Raises:
            DatiNonValidi: il dato non è un comando valido.
        """
        try:
            f = dati.get("finestra")
            if isinstance(f, dict) and f.get("regole") == "r42":
                finestra: RegoleR42 | Finestra | None = RegoleR42(
                    canale=f["canale"],
                    proporzione=f.get("proporzione"),
                    soggetto_box=f.get("soggetto_box"),
                )
            elif isinstance(f, dict):
                finestra = Finestra(b=tuple(f["b"]), rapporto=float(f["rapporto"]))
            else:
                finestra = None
            return cls(
                versione=dati["versione"],
                ruota=dati["ruota"],
                raddrizza=dati.get("raddrizza"),
                finestra=finestra,
                barre=dati.get("barre"),
                luce=dati.get("luce"),
                nitidezza=bool(dati.get("nitidezza")),
                nitidezza_dose=float(
                    dati.get("nitidezza_dose", catalogo.STANDARD.nitidezza_dose)
                ),
            )
        except (KeyError, TypeError, ValueError, AttributeError) as errore:
            raise DatiNonValidi("Comando di ritocco non valido.") from errore

    def __post_init__(self) -> None:
        if self.barre not in (None, "sfocate", "neutre"):
            raise DatiNonValidi(f"Barre '{self.barre}' non ammesse: sfocate o neutre.")
        if isinstance(self.finestra, Finestra):
            x, y, w, h = self.finestra.b
            if not (0 <= x < 1 and 0 <= y < 1 and w > 0 and h > 0):
                raise DatiNonValidi("La finestra deve stare dentro la foto.")
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
    dati: bytes = b""
    # Falso dopo le regole di R-42: non dicono dove sono finiti i punti (luce senza regione).
    mappa_affidabile: bool = True


_Passo = Callable[[Image.Image, Comando, "str | None", _Contesto], Image.Image]


def _passo_ruota(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    img, ctx.mappa = geometria.ruota_90(img, comando.ruota, ctx.mappa)
    return img


def _passo_privacy(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    """Sfoca le zone attive nel riferimento dell'originale, già ruotato di 90° (RT-18)."""
    if not ctx.zone:
        return img
    return privacy.oscura_zone(img.copy(), ctx.zone, ctx.mappa)


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


def _applica_finestra(
    img: Image.Image, finestra: Finestra, barre: str | None, ctx: _Contesto
) -> Image.Image:
    """Ritaglia il riquadro calcolato; se il rapporto esce dall'intervallo, barre (o, senza, taglio al centro)."""
    larghezza, altezza = img.size
    x, y, w, h = finestra.b
    x0, y0 = min(larghezza - 1, max(0, round(x * larghezza))), min(
        altezza - 1, max(0, round(y * altezza))
    )
    x1, y1 = max(x0 + 1, min(larghezza, round((x + w) * larghezza))), max(
        y0 + 1, min(altezza, round((y + h) * altezza))
    )
    ritagliata = (
        img.crop((x0, y0, x1, y1))
        if (x0, y0, x1, y1) != (0, 0, larghezza, altezza)
        else img
    )
    rapporto = ritagliata.width / ritagliata.height
    tolleranza = regole.TOLLERANZA_PROPORZIONE
    if (
        regole.RATIO_MINIMO - tolleranza
        <= rapporto
        <= regole.RATIO_MASSIMO + tolleranza
    ):
        return ritagliata
    target = (
        regole.RATIO_MINIMO if rapporto < regole.RATIO_MINIMO else regole.RATIO_MASSIMO
    )
    if barre is None:  # difesa: un comando senza barre non esce mai dall'intervallo
        return regole._ritaglia_al_centro(ritagliata, target)
    return regole.tela_con_barre(ritagliata, target, neutre=barre == "neutre")


def _passo_finestra(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    """Le regole di R-42: rapporto più vicino nell'intervallo, soggetto, centro, bordi sfocati."""
    if isinstance(comando.finestra, Finestra):
        return _applica_finestra(img, comando.finestra, comando.barre, ctx)
    r42 = comando.finestra
    if r42 is None or canale is None:
        return img
    ctx.mappa_affidabile = False
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
    ridimensionata = regole._ridimensiona_lato_corto(img, regole.LATO_CORTO_TARGET)
    if ridimensionata.size != img.size:
        ctx.mappa = ctx.mappa.scalata(*ridimensionata.size)
    return ridimensionata


def _passo_luce(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    """Esposizione, bianco, ombre e flash, misurati nella regione del soggetto (RT-17)."""
    if not comando.luce:
        return img
    luce = comando.luce
    soggetto = neutro = None
    if ctx.mappa_affidabile:
        soggetto = ctx.mappa.box_norm(luce.get("soggetto"))
        neutro = ctx.mappa.box_norm((luce.get("bianco") or {}).get("neutro"))
    return luce_foto.correggi_luce(img, luce, soggetto, neutro)


def _passo_nitidezza(
    img: Image.Image, comando: Comando, canale: str | None, ctx: _Contesto
) -> Image.Image:
    """Una nitidezza leggera, solo dove non peggiora la foto (RT-17)."""
    if not comando.nitidezza:
        return img
    fatti = fatti_del_file(ctx.dati)
    zoom = fatti["exif"]["zoom_digitale"]
    qualita = fatti["qualita_jpeg"]
    if (qualita is not None and qualita < catalogo.NITIDEZZA_QUALITA_MIN) or (
        zoom is not None and zoom > catalogo.NITIDEZZA_ZOOM_MAX
    ):
        ctx.avvisi.append("nitidezza_saltata")
        return img
    return luce_foto.nitidezza(img, comando.nitidezza_dose)


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
    canale = (
        _canale_valido(comando.finestra.canale)
        if isinstance(comando.finestra, RegoleR42)
        else None
    )
    passi = traccia if traccia is not None else []

    # 1-2. Decodifica, EXIF e sRGB: una funzione sola per tutte le foto (RT-02).
    # Il limite si legge qui, a ogni chiamata (così i test lo possono abbassare).
    img = apri_in_srgb(dati, max_pixel=regole.MAX_PIXEL_TOTALI)
    passi.extend(("decodifica", "srgb"))
    ctx = _Contesto(geometria.Mappa.identita(*img.size), zone_privacy, dati=dati)

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
