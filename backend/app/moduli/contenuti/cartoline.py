"""Cartoline: l'immagine dei post riempitivo, composta dal sistema (spec R-28).

Una cartolina è un quadrato di 1080 px con il tema dell'uscita e il nome della
bottega. Non passa dall'AI. Dalla 2a porterà anche il logo, se c'è.

Il carattere è Lato Regular, in ``font/`` con la sua licenza (SIL OFL 1.1):
quello incluso in Pillow non ha le lettere accentate.
"""

import unicodedata
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.adapters.archivio import ottieni_archivio
from app.moduli.campagne import service as campagne

LATO = 1080
MIME = "image/png"
ESTENSIONE = "png"

_MARGINE = 108
_SFONDO = (245, 240, 232)
_INCHIOSTRO = (51, 43, 38)
_ACCENTO = (176, 92, 52)
_CORPI_DEL_TEMA = (96, 84, 72, 64, 56, 48)
_CORPI_DEL_NOME = (54, 46, 40, 34)
_MAX_RIGHE = 5
_INTERLINEA = 1.25
_FONT = Path(__file__).parent / "font" / "Lato-Regular.ttf"


@lru_cache(maxsize=None)
def _carattere(corpo: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(_FONT), corpo)


@lru_cache(maxsize=None)
def _si_disegna(lettera: str) -> bool:
    """Vero se il carattere ha un disegno per la lettera (non il quadratino)."""
    carattere = _carattere(32)
    return bytes(carattere.getmask(lettera)) != bytes(carattere.getmask("￿"))


def _pulito(testo: str | None) -> str:
    """Spazi semplici e solo lettere che il carattere sa disegnare.

    Una lettera che manca (un'emoji, un alfabeto diverso) diventa la sua
    lettera di base, se c'è, altrimenti si toglie: mai un quadratino vuoto.
    """
    lettere = []
    for lettera in " ".join((testo or "").split()):
        if lettera == " " or _si_disegna(lettera):
            lettere.append(lettera)
            continue
        base = unicodedata.normalize("NFD", lettera)[0]
        if base != lettera and _si_disegna(base):
            lettere.append(base)
    return " ".join("".join(lettere).split())


def _righe(
    disegno: ImageDraw.ImageDraw,
    testo: str,
    carattere: ImageFont.FreeTypeFont,
    larghezza: int,
) -> list[str]:
    """Il testo a capo parola per parola, dentro la larghezza."""
    righe: list[str] = []
    for parola in testo.split():
        prova = f"{righe[-1]} {parola}" if righe else parola
        if righe and disegno.textlength(prova, font=carattere) <= larghezza:
            righe[-1] = prova
        else:
            righe.append(parola)
    return righe


def _accorcia(
    disegno: ImageDraw.ImageDraw,
    testo: str,
    carattere: ImageFont.FreeTypeFont,
    larghezza: int,
) -> str:
    """Il testo tagliato con i puntini, finché entra nella larghezza."""
    if disegno.textlength(testo, font=carattere) <= larghezza:
        return testo
    while testo and disegno.textlength(f"{testo}…", font=carattere) > larghezza:
        testo = testo[:-1].rstrip()
    return f"{testo}…"


def _componi_il_tema(
    disegno: ImageDraw.ImageDraw, tema: str, larghezza: int
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Il corpo più grande con cui il tema sta in poche righe; poi si taglia."""
    for corpo in _CORPI_DEL_TEMA:
        carattere = _carattere(corpo)
        righe = _righe(disegno, tema, carattere, larghezza)
        entra = all(disegno.textlength(r, font=carattere) <= larghezza for r in righe)
        if entra and len(righe) <= _MAX_RIGHE:
            return carattere, righe
    tagliate = [_accorcia(disegno, r, carattere, larghezza) for r in righe]
    if len(tagliate) > _MAX_RIGHE:
        tagliate = tagliate[:_MAX_RIGHE]
        tagliate[-1] = _accorcia(disegno, f"{tagliate[-1]} …", carattere, larghezza)
    return carattere, tagliate


def disegna_cartolina(nome_bottega: str | None, tema: str | None) -> bytes:
    """Compone la cartolina e ne restituisce il file PNG, 1080 × 1080 px.

    Funzione pura: lo stesso risultato a parità di testi. Un tema lungo si
    rimpicciolisce e poi si taglia; senza tema o senza nome la cartolina esce
    con ciò che c'è.
    """
    nome = _pulito(nome_bottega)
    tema = _pulito(tema)
    immagine = Image.new("RGB", (LATO, LATO), _SFONDO)
    disegno = ImageDraw.Draw(immagine)
    larghezza = LATO - 2 * _MARGINE
    centro = LATO // 2

    disegno.rectangle(
        (_MARGINE // 2, _MARGINE // 2, LATO - _MARGINE // 2, LATO - _MARGINE // 2),
        outline=_ACCENTO,
        width=4,
    )

    if tema:
        carattere, righe = _componi_il_tema(disegno, tema, larghezza)
        passo = int(carattere.size * _INTERLINEA)
        y = centro - (passo * len(righe)) // 2 - (60 if nome else 0)
        for riga in righe:
            disegno.text(
                (centro, y), riga, font=carattere, fill=_INCHIOSTRO, anchor="ma"
            )
            y += passo

    if nome:
        for corpo in _CORPI_DEL_NOME:
            carattere = _carattere(corpo)
            if disegno.textlength(nome, font=carattere) <= larghezza:
                break
        nome = _accorcia(disegno, nome, carattere, larghezza)
        y = LATO - _MARGINE - 110 if tema else centro
        disegno.line((centro - 60, y - 36, centro + 60, y - 36), fill=_ACCENTO, width=4)
        disegno.text((centro, y), nome, font=carattere, fill=_ACCENTO, anchor="ma")

    file = BytesIO()
    immagine.save(file, format="PNG", optimize=True)
    return file.getvalue()


def componi_cartolina(db: Session, campagna: Any, tema: str | None) -> Any:
    """Crea la foto di un post `cartolina` e la restituisce, senza commit.

    Il nome della bottega viene dalla fotografia del profilo salvata all'invio
    (``campagna.profilo_snapshot``), mai dal profilo corrente. Il file va
    nell'archivio con un nome generato dal server; la foto nasce senza gruppo,
    con origine ``cartolina`` (``campagne.service.aggiungi_foto()``).

    Se la foto non si crea, il file appena salvato si elimina. Se la
    transazione di chi chiama viene annullata più tardi, il file resta
    nell'archivio senza una foto: è un file orfano, innocuo.
    """
    snapshot = campagna.profilo_snapshot
    nome = snapshot.get("nome") if isinstance(snapshot, dict) else None
    archivio = ottieni_archivio()
    file = archivio.salva(disegna_cartolina(nome, tema), ESTENSIONE)
    try:
        return campagne.aggiungi_foto(
            db, campagna.id, "cartolina", file, MIME, LATO, LATO
        )
    except Exception:
        archivio.elimina(file)
        raise
