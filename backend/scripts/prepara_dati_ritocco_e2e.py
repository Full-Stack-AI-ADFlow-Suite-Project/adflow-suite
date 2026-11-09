"""Dati di prova del ritocco per il percorso end-to-end (RT-10, ADR-124).

Da ``backend/``, sul database già migrato e col seed fatto (lo prepara
``frontend/e2e/prepara-backend.sh``)::

    uv run python scripts/prepara_dati_ritocco_e2e.py

Crea per l'artigiano del seed una campagna con quattro foto sintetiche (una in
Display P3, una storta, una buia, una buona), la invia e la genera con l'AI
finta fino alla revisione: l'operatore la trova in «Campagne da approvare».
Nessuna foto vera, nessuna chiamata di rete. Le foto sono generate con gli
stessi strumenti dei test (``tests/immagini.py``).
"""

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.cli import UTENTI_SEED, esegui_prova_ai  # noqa: E402
from app.core.config import leggi_impostazioni  # noqa: E402
from app.core.db import transazione  # noqa: E402
from app.core.orologio import ROMA, adesso  # noqa: E402
from app.moduli.accesso.models import Utente  # noqa: E402
from app.moduli.campagne import service as campagne  # noqa: E402
from app.moduli.campagne.schemas import CampagnaCrea, GruppoCrea  # noqa: E402
from tests import immagini  # noqa: E402

TITOLO = "Campagna del ritocco"
DIMENSIONI = (1600, 1200)


def foto_sintetiche() -> dict[str, bytes]:
    """Quattro JPEG con lato corto >= 1080: p3, storta, buia, buona."""
    p3 = immagini.gradiente(DIMENSIONI, (230, 40, 20), (250, 200, 60))
    storta, _ = immagini.rettangolo_inclinato(DIMENSIONI, 4.0, (1000, 700))
    buia = immagini.gradiente(DIMENSIONI, (5, 5, 8), (60, 50, 45))
    buona = immagini.gradiente(DIMENSIONI, (70, 90, 120), (190, 170, 140))
    return {
        "p3": immagini.jpeg_con_exif(p3, profilo=immagini.profilo_icc("p3")),
        "storta": immagini.jpeg_qualita(storta, 92),
        "buia": immagini.jpeg_qualita(buia, 92),
        "buona": immagini.jpeg_qualita(buona, 92),
    }


def main() -> int:
    ora = adesso()
    email_artigiano = next(e for e, _, ruolo in UTENTI_SEED if ruolo == "artigiano")
    anticipo = leggi_impostazioni().anticipo_minimo_giorni
    inizio = ora.astimezone(ROMA).date() + timedelta(days=anticipo + 1)
    with transazione() as db:
        artigiano = db.scalar(select(Utente).where(Utente.email == email_artigiano))
        if artigiano is None:
            print("Manca il seed: lancia prima `python -m app.cli seed`.")
            return 1
        campagna = campagne.crea_bozza(
            db,
            artigiano.id,
            CampagnaCrea(
                titolo=TITOLO,
                descrizione="Foto sintetiche per provare il ritocco.",
                canali=["facebook", "instagram"],
                inizio=inizio,
                fine=inizio + timedelta(days=6),
            ),
            ora,
        )
        gruppo = campagne.crea_gruppo(
            db,
            artigiano.id,
            "artigiano",
            campagna.id,
            GruppoCrea(descrizione="Foto sintetiche del ritocco"),
        )
        for contenuto in foto_sintetiche().values():
            campagne.carica_foto(
                db, artigiano.id, "artigiano", campagna.id, contenuto, gruppo.id
            )
        campagne.invia_campagna(db, artigiano.id, campagna.id, ora, dichiarazione=True)
        campagna_id = campagna.id

    esito = esegui_prova_ai(campagna_id)
    if esito.errore is not None:
        print(f"Generazione non riuscita: {esito.errore}")
        return 1
    print(f"Campagna {campagna_id} «{TITOLO}» pronta: stato {esito.stato}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
