"""L'archivio foto in sola lettura, a blocchi per campagna (spec R-47, ADR-117).

Per l'artigiano le sue foto, per l'operatore quelle dell'artigiano che indica.
Sono le foto ``caricata`` e ``creata_ai`` del profilo; le ``cartolina`` mai.
Prima dell'approvazione l'artigiano non vede il piano (spec §4, CA-31): le
immagini AI gli compaiono solo con le campagne approvate. Non scrive niente:
l'archivio modificabile (``archivio.py``) resta congelato (ADR-114).
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errori import DatiNonValidi
from app.moduli.artigiani import service as artigiani

from . import domain, service
from .models import Campagna, Foto
from .schemas import BloccoArchivio, CampagnaDelBlocco, FotoArchivio

_ORIGINI_VISIBILI = ("caricata", "creata_ai")
# Le campagne approvate: da qui in poi l'artigiano vede anche le immagini AI.
_STATI_APPROVATE = (
    domain.ATTIVA,
    domain.SOSPESA,
    domain.CONCLUSA,
    domain.ANNULLATA,
)


def _foto_archivio(foto: Foto) -> FotoArchivio:
    return FotoArchivio(
        id=foto.id,
        url=f"/api/foto/{foto.id}/file",
        origine=foto.origine,
        mime=foto.mime,
        larghezza=foto.larghezza,
        altezza=foto.altezza,
        pubblicata_su={
            canale: datetime.fromisoformat(quando)
            for canale, quando in (foto.pubblicata_su or {}).items()
        },
    )


def leggi(
    db: Session, utente_id: int, ruolo: str, artigiano: int | None = None
) -> list[BloccoArchivio]:
    """I blocchi dell'archivio, dalla campagna più recente (CA-95, CA-96).

    Raises:
        DatiNonValidi: operatore o admin senza ``artigiano`` (422).
        NonTrovato: ``artigiano`` non è l'id di un artigiano (404).
    """
    if ruolo == "artigiano":
        # Il parametro non conta: l'artigiano vede solo le sue foto.
        proprietario = utente_id
    else:
        if artigiano is None:
            raise DatiNonValidi("Indica l'artigiano di cui vedere le foto.")
        proprietario = service.utente_artigiano(db, artigiano)
    bottega = artigiani.profilo_di(db, proprietario)
    if bottega is None:
        return []

    foto = list(
        db.scalars(
            select(Foto)
            .where(Foto.profilo_id == bottega.id, Foto.origine.in_(_ORIGINI_VISIBILI))
            .order_by(Foto.id)
        )
    )
    ids_campagne = {f.campagna_id for f in foto if f.campagna_id is not None}
    campagne = {
        c.id: c
        for c in db.scalars(select(Campagna).where(Campagna.id.in_(ids_campagne)))
    }

    per_campagna: dict[int | None, list[Foto]] = {}
    for immagine in foto:
        campagna = campagne.get(immagine.campagna_id)
        if (
            ruolo == "artigiano"
            and immagine.origine == "creata_ai"
            and (campagna is None or campagna.stato not in _STATI_APPROVATE)
        ):
            continue
        per_campagna.setdefault(immagine.campagna_id, []).append(immagine)

    blocchi = [
        BloccoArchivio(
            campagna=CampagnaDelBlocco(
                id=campagna.id,
                titolo=campagna.titolo,
                stato=campagna.stato,
                inizio=campagna.inizio,
                fine=campagna.fine,
            ),
            foto=[_foto_archivio(f) for f in per_campagna[campagna.id]],
        )
        for campagna in sorted(campagne.values(), key=lambda c: -c.id)
        if campagna.id in per_campagna
    ]
    if None in per_campagna:
        blocchi.append(
            BloccoArchivio(
                campagna=None, foto=[_foto_archivio(f) for f in per_campagna[None]]
            )
        )
    return blocchi
