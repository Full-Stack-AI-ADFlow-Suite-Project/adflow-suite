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
from app.moduli.accesso import service as accesso
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti

from .schemas import ArtigianoElenco, CampagnaDaApprovare, ConteggiPost

# Spec §4: gli stati della sezione «Da approvare» e di «In corso».
_STATI_DA_APPROVARE = (
    "inviata",
    "in_generazione",
    "piano_da_rivedere",
    "generazione_fallita",
    "in_revisione",
)
_STATI_IN_CORSO = ("attiva", "sospesa")


def _entro_quando(campagna, post) -> datetime:
    """Entro quando la campagna va approvata (spec R-38).

    La data del primo post ``da_approvare``; se il piano non c'è, le 00:00
    (Europe/Rome) del giorno di inizio.
    """
    prima_uscita = min(
        (p.data_ora for p in post if p.stato == "da_approvare"), default=None
    )
    return prima_uscita or datetime.combine(campagna.inizio, time.min, tzinfo=ROMA)


def elenco_artigiani(db: Session) -> list[ArtigianoElenco]:
    """Tutti gli artigiani con la situazione delle loro campagne (spec R-38, CA-92).

    Prima chi ha la scadenza più vicina (chi non ne ha va in fondo), poi per
    bottega, o per nome dell'account se il profilo manca, senza maiuscole.
    """
    righe: list[ArtigianoElenco] = []
    for utente in accesso.artigiani(db):
        bottega = artigiani.profilo_di(db, utente.id)
        da_approvare_ora = []
        n_in_corso = 0
        if bottega is not None:
            for campagna in campagne.campagne_di(db, bottega.id):
                if campagna.stato in _STATI_DA_APPROVARE:
                    post = contenuti.post_della_campagna(db, campagna.id)
                    da_approvare_ora.append(_entro_quando(campagna, post))
                elif campagna.stato in _STATI_IN_CORSO:
                    n_in_corso += 1
        righe.append(
            ArtigianoElenco(
                id=utente.id,
                nome=utente.nome,
                email=utente.email,
                attivo=utente.attivo,
                bottega=bottega.nome if bottega is not None else None,
                referente=bottega.referente if bottega is not None else None,
                citta=bottega.citta if bottega is not None else None,
                canali_collegati=(
                    artigiani.canali_collegati(db, bottega.id)
                    if bottega is not None
                    else []
                ),
                n_da_approvare=len(da_approvare_ora),
                n_in_corso=n_in_corso,
                prossima_scadenza=min(da_approvare_ora, default=None),
            )
        )
    righe.sort(
        key=lambda r: (
            r.prossima_scadenza is None,
            r.prossima_scadenza.timestamp() if r.prossima_scadenza else 0.0,
            (r.bottega or r.nome).casefold(),
        )
    )
    return righe


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
        nota = campagne.ultima_nota(db, campagna.id)
        bottega = artigiani.profilo(db, campagna.profilo_id)
        richiesta = campagne.richiesta_di(db, campagna.id)
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
                entro_quando=_entro_quando(campagna, post),
                ultima_nota=nota.nota if nota is not None else None,
                richiesta=(
                    richiesta.stato
                    if richiesta is not None and richiesta.stato != "decaduta"
                    else None
                ),
            )
        )
    righe.sort(key=lambda riga: riga.entro_quando)
    return righe
