"""Calendario settimanale, da lunedì a domenica (spec R-45, R-48, ADR-117).

L'artigiano vede i post delle sue campagne, l'operatore quelli di tutti gli
artigiani. Sono i post approvati, pubblicati, falliti o annullati delle
campagne approvate; la settimana è sempre di sette giorni, in Europe/Rome.
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errori import DatiNonValidi
from app.core.orologio import ROMA
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne

from .calendario import STATI_VISIBILI, costruisci_post, immagini_dei_post
from .models import Post, VersionePost
from .schemas import CalendarioSettimana, GiornoSettimana, PostSettimana

# Le campagne approvate, per nome: il domain.py di un altro modulo non si importa.
_STATI_CAMPAGNA = ["attiva", "sospesa", "conclusa", "annullata"]


def _lunedi(giorno: date) -> date:
    return giorno - timedelta(days=giorno.weekday())


def leggi(
    db: Session,
    utente_id: int,
    ruolo: str,
    dal: date | None,
    adesso: datetime,
) -> CalendarioSettimana:
    """La settimana che comincia a ``dal``; senza data, quella di ``adesso``.

    Raises:
        DatiNonValidi: ``dal`` non è un lunedì (422).
    """
    if dal is None:
        dal = _lunedi(adesso.astimezone(ROMA).date())
    elif dal.weekday() != 0:
        raise DatiNonValidi("La settimana comincia di lunedì.")
    al = dal + timedelta(days=6)

    if ruolo == "artigiano":
        bottega = artigiani.profilo_di(db, utente_id)
        elenco = (
            campagne.campagne_di(db, bottega.id, _STATI_CAMPAGNA)
            if bottega is not None
            else []
        )
    else:
        elenco = campagne.campagne_in_stato(db, _STATI_CAMPAGNA)
    per_id = {c.id: c for c in elenco}

    post: list[Post] = []
    if per_id:
        post = list(
            db.scalars(
                select(Post)
                .where(
                    Post.campagna_id.in_(list(per_id)),
                    Post.stato.in_(STATI_VISIBILI),
                    Post.data_ora >= datetime.combine(dal, time.min, tzinfo=ROMA),
                    Post.data_ora
                    < datetime.combine(al + timedelta(days=1), time.min, tzinfo=ROMA),
                )
                .options(
                    selectinload(Post.versioni).selectinload(VersionePost.legami_foto)
                )
                .order_by(Post.data_ora, Post.id)
            )
        )
    immagini = immagini_dei_post(db, post)

    botteghe: dict[int, str | None] = {}
    giorni: dict[date, list[PostSettimana]] = {
        dal + timedelta(days=i): [] for i in range(7)
    }
    for p in post:
        campagna = per_id[p.campagna_id]
        if campagna.profilo_id not in botteghe:
            profilo = artigiani.profilo(db, campagna.profilo_id)
            botteghe[campagna.profilo_id] = profilo.nome if profilo else None
        base = costruisci_post(p, immagini, campagna.profilo_id)
        giorni[p.data_ora.astimezone(ROMA).date()].append(
            PostSettimana(
                **base.model_dump(),
                campagna_id=campagna.id,
                campagna_titolo=campagna.titolo,
                bottega=botteghe[campagna.profilo_id],
            )
        )
    return CalendarioSettimana(
        dal=dal,
        al=al,
        giorni=[GiornoSettimana(data=g, post=giorni[g]) for g in sorted(giorni)],
    )
