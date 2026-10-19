"""Le viste della campagna per l'artigiano (spec §4).

Nell'elenco la pagina apre la campagna che chiede qualcosa: quella in
revisione con una richiesta del consorzio aperta (R-46), poi la bozza, poi
una ``respinta`` o ``scaduta`` non ancora sostituita, poi quella in corso,
poi quella in lavorazione; in fondo le "campagne passate". Nel dettaglio
l'artigiano non legge mai le note interne né la fotografia del profilo:
restano solo le decisioni ``canale_tolto`` con la nota dell'operatore e,
su una ``respinta``, motivo, nota e foto da rifare (R-18, R-32).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import domain, service
from .models import DecisioneCampagna
from .schemas import (
    CampagnaDettaglio,
    CampagnaElencoItem,
    DecisioneSintetica,
    EsitoRespinta,
)

_IN_CORSO = (domain.ATTIVA, domain.SOSPESA)
_IN_LAVORAZIONE = (
    domain.INVIATA,
    domain.IN_GENERAZIONE,
    domain.GENERAZIONE_FALLITA,
    domain.PIANO_DA_RIVEDERE,
    domain.IN_REVISIONE,
)


def _priorita(
    campagna: CampagnaElencoItem, tutte: list[CampagnaElencoItem]
) -> int | None:
    """Quanto prima si apre la campagna; ``None`` la manda nelle passate."""
    if campagna.richiesta == "aperta":
        return -1
    if campagna.stato == domain.BOZZA:
        return 0
    if campagna.stato in (domain.RESPINTA, domain.SCADUTA):
        # Resta finché l'artigiano crea una nuova campagna: se ce n'è una più
        # recente (l'ordine di creazione è l'id), questa è stata sostituita.
        if any(altra.id > campagna.id for altra in tutte):
            return None
        return 1
    if campagna.stato in _IN_CORSO:
        return 2
    if campagna.stato in _IN_LAVORAZIONE:
        return 3
    return None


def campagne_artigiano(
    db: Session,
    utente_id: int,
    stati: list[str] | None = None,
) -> list[CampagnaElencoItem]:
    """Le campagne dell'artigiano nell'ordine di apertura della pagina (§4)."""
    lista = service.elenca_campagne(db, utente_id, "artigiano", stati)
    for voce in lista:
        if voce.stato == domain.IN_REVISIONE:
            richiesta = service.richiesta_di(db, voce.id)
            voce.richiesta = richiesta.stato if richiesta is not None else None
    ordinate = [(c, _priorita(c, lista)) for c in lista]
    da_aprire = sorted(
        ((c, p) for c, p in ordinate if p is not None),
        key=lambda voce: (voce[1], -voce[0].id),
    )
    passate = sorted((c for c, p in ordinate if p is None), key=lambda c: -c.id)
    return [c for c, _ in da_aprire] + passate


def dettaglio_artigiano(
    db: Session,
    utente_id: int,
    campagna_id: int,
) -> CampagnaDettaglio:
    """Il dettaglio come lo vede l'artigiano proprietario (CA-31, CA-53).

    404 se la campagna è di un altro artigiano (gestito da ``dettaglio_campagna``).
    """
    dettaglio = service.dettaglio_campagna(db, utente_id, "artigiano", campagna_id)
    dettaglio.decisioni = [
        DecisioneSintetica.model_validate(d)
        for d in db.scalars(
            select(DecisioneCampagna)
            .where(
                DecisioneCampagna.campagna_id == campagna_id,
                DecisioneCampagna.esito == "canale_tolto",
            )
            .order_by(DecisioneCampagna.id)
        )
    ]
    if dettaglio.stato == domain.RESPINTA:
        respinta = db.scalar(
            select(DecisioneCampagna)
            .where(
                DecisioneCampagna.campagna_id == campagna_id,
                DecisioneCampagna.esito == domain.ESITO_RESPINTA,
            )
            .order_by(DecisioneCampagna.id.desc())
            .limit(1)
        )
        if respinta is not None:
            dettaglio.esito_respinta = EsitoRespinta(
                motivo=respinta.motivo or "altro",
                nota=respinta.nota,
                foto_segnate=list(respinta.foto_segnate or []),
            )
    return dettaglio
