"""La pagina «Campagne da approvare» dell'operatore (spec §4, R-38).

Contiene le campagne di tutti gli artigiani negli stati della sezione
«Da approvare», ordinate dalla più urgente: ``entro_quando`` è la data del
primo post ``da_approvare``, oppure le 00:00 (Europe/Rome) del giorno di
inizio se il piano non c'è. Ogni riga porta bottega e città, i conteggi dei
post e l'ultima nota interna.
"""

from datetime import datetime, time

from sqlalchemy.orm import Session

from app.core.orologio import ROMA
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti

from .schemas import CampagnaDaApprovare, ConteggiPost

# Spec §4: gli stati della sezione «Da approvare».
_STATI_DA_APPROVARE = (
    "inviata",
    "in_generazione",
    "piano_da_rivedere",
    "generazione_fallita",
    "in_revisione",
)


def da_approvare(db: Session) -> list[CampagnaDaApprovare]:
    """Le campagne da approvare di tutti gli artigiani, dalla più urgente (CA-69)."""
    righe: list[CampagnaDaApprovare] = []
    for campagna in campagne.campagne_in_stato(db, list(_STATI_DA_APPROVARE)):
        post = contenuti.post_della_campagna(db, campagna.id)
        in_attesa = [p for p in post if p.stato == "da_approvare"]
        riempitivi: dict[str, int] = {}
        for p in post:
            if p.riempitivo:
                riempitivi[p.canale] = riempitivi.get(p.canale, 0) + 1
        prima_uscita = min((p.data_ora for p in in_attesa), default=None)
        nota = campagne.ultima_nota(db, campagna.id)
        bottega = artigiani.profilo(db, campagna.profilo_id)
        righe.append(
            CampagnaDaApprovare(
                id=campagna.id,
                profilo_id=campagna.profilo_id,
                titolo=campagna.titolo,
                inizio=campagna.inizio,
                fine=campagna.fine,
                stato=campagna.stato,
                canali=campagna.canali,
                bottega=bottega.nome if bottega is not None else None,
                citta=bottega.citta if bottega is not None else None,
                conteggi=ConteggiPost(
                    totale=len(post),
                    da_approvare=len(in_attesa),
                    da_rivedere=sum(1 for p in in_attesa if p.da_rivedere),
                    riempitivi=riempitivi,
                ),
                entro_quando=prima_uscita
                or datetime.combine(campagna.inizio, time.min, tzinfo=ROMA),
                ultima_nota=nota.nota if nota is not None else None,
            )
        )
    righe.sort(key=lambda riga: riga.entro_quando)
    return righe
