"""Le letture dell'operatore (spec §4, plan §3).

«Campagne da approvare»: le campagne di tutti gli artigiani negli stati della
sezione «Da approvare», ordinate dalla più urgente: ``entro_quando`` è la
data del primo post ``da_approvare``, oppure le 00:00 (Europe/Rome) del
giorno di inizio se il piano non c'è. Ogni riga porta bottega e città, i
conteggi dei post e l'ultima nota interna.

«Elenco artigiani» e «scheda artigiano``: tutti gli artigiani del consorzio
con la loro situazione e, per uno, il dettaglio per sezioni: campagne da
approvare, in corso, le ultime tre chiuse e il totale delle chiuse.
"""

from datetime import datetime, time, timezone

from sqlalchemy.orm import Session

from app.core.errori import NonTrovato
from app.core.orologio import ROMA
from app.moduli.accesso import service as accesso
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti

from .schemas import (
    ArtigianoElenco,
    CampagnaDaApprovare,
    CampagnaSezione,
    ConteggiPost,
    ProfiloArtigiano,
    SchedaArtigiano,
    UtenteArtigiano,
)

# Spec §4 e ADR-53: gli stati delle sezioni della scheda artigiano.
_STATI_DA_APPROVARE = (
    "inviata",
    "in_generazione",
    "piano_da_rivedere",
    "generazione_fallita",
    "in_revisione",
)
_STATI_IN_CORSO = ("attiva", "sospesa")
_STATI_CHIUSE = ("scaduta", "conclusa", "annullata", "respinta")

# Nella scheda le campagne chiuse si mostrano solo per le ultime tre.
_CHIUSE_IN_SCHEDA = 3


def _entro_quando(db: Session, campagna) -> datetime:
    """La data del primo post ``da_approvare``, o le 00:00 dell'inizio (R-38)."""
    post = contenuti.post_della_campagna(db, campagna.id)
    prima = min(
        (uno.data_ora for uno in post if uno.stato == "da_approvare"),
        default=None,
    )
    return prima or datetime.combine(campagna.inizio, time.min, tzinfo=ROMA)


def _riga_da_approvare(db: Session, campagna) -> CampagnaDaApprovare:
    """La riga di una campagna «da approvare»: conteggi, entro quando, nota."""
    post = contenuti.post_della_campagna(db, campagna.id)
    in_attesa = [uno for uno in post if uno.stato == "da_approvare"]
    riempitivi: dict[str, int] = {}
    for uno in post:
        if uno.riempitivo:
            riempitivi[uno.canale] = riempitivi.get(uno.canale, 0) + 1
    nota = campagne.ultima_nota(db, campagna.id)
    bottega = artigiani.profilo(db, campagna.profilo_id)
    richiesta = campagne.richiesta_di(db, campagna.id)
    return CampagnaDaApprovare(
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
            da_rivedere=sum(1 for uno in in_attesa if uno.da_rivedere),
            riempitivi=riempitivi,
        ),
        entro_quando=min((uno.data_ora for uno in in_attesa), default=None)
        or datetime.combine(campagna.inizio, time.min, tzinfo=ROMA),
        ultima_nota=nota.nota if nota is not None else None,
        richiesta=(
            richiesta.stato
            if richiesta is not None and richiesta.stato != "decaduta"
            else None
        ),
    )


def _sezione(db: Session, campagna) -> CampagnaSezione:
    """La riga compatta di una campagna nelle sezioni della scheda artigiano."""
    post = contenuti.post_della_campagna(db, campagna.id)
    return CampagnaSezione(
        id=campagna.id,
        titolo=campagna.titolo,
        stato=campagna.stato,
        inizio=campagna.inizio,
        fine=campagna.fine,
        canali=campagna.canali,
        inviata_il=campagna.inviata_il,
        chiusa_il=campagna.chiusa_il,
        n_post=len(post),
        n_pubblicati=sum(1 for uno in post if uno.stato == "pubblicato"),
        n_falliti=sum(1 for uno in post if uno.stato == "fallito"),
        n_foto=len(campagne.foto_della_campagna(db, campagna.id)),
    )


def da_approvare(db: Session) -> list[CampagnaDaApprovare]:
    """Le campagne da approvare di tutti gli artigiani, dalla più urgente (CA-69)."""
    righe = [
        _riga_da_approvare(db, campagna)
        for campagna in campagne.campagne_in_stato(db, list(_STATI_DA_APPROVARE))
    ]
    righe.sort(key=lambda riga: riga.entro_quando)
    return righe


def elenco_artigiani(db: Session) -> list[ArtigianoElenco]:
    """Tutti gli artigiani del consorzio, dalla scadenza più vicina.

    Ogni riga porta account, profilo (se compilato), canali collegati e il
    quadro delle campagne: quante da approvare, quante in corso e la scadenza
    più vicina (``entro_quando`` della campagna da approvare più urgente).
    Chi non ha una scadenza va in fondo, in ordine di bottega.
    """
    righe: list[ArtigianoElenco] = []
    for record in accesso.artigiani(db):
        profilo = artigiani.profilo_di(db, record.id)
        n_da_approvare = 0
        n_in_corso = 0
        prossima: tuple[datetime, int] | None = None
        if profilo is not None:
            for campagna in campagne.campagne_di(db, profilo.id):
                if campagna.stato in _STATI_DA_APPROVARE:
                    n_da_approvare += 1
                    entro = _entro_quando(db, campagna)
                    if prossima is None or entro < prossima[0]:
                        prossima = (entro, campagna.id)
                elif campagna.stato in _STATI_IN_CORSO:
                    n_in_corso += 1
        righe.append(
            ArtigianoElenco(
                id=record.id,
                email=record.email,
                nome=record.nome,
                attivo=record.attivo,
                profilo_id=profilo.id if profilo is not None else None,
                bottega=profilo.nome if profilo is not None else None,
                citta=profilo.citta if profilo is not None else None,
                tipo_prodotto=(profilo.tipo_prodotto if profilo is not None else None),
                canali_collegati=(
                    artigiani.canali_collegati(db, profilo.id)
                    if profilo is not None
                    else []
                ),
                n_da_approvare=n_da_approvare,
                n_in_corso=n_in_corso,
                prossima_scadenza=prossima[0] if prossima else None,
                prossima_campagna_id=prossima[1] if prossima else None,
            )
        )
    lontano = datetime.max.replace(tzinfo=timezone.utc)
    righe.sort(
        key=lambda riga: (
            riga.prossima_scadenza or lontano,
            (riga.bottega or riga.nome).lower(),
        )
    )
    return righe


def scheda_artigiano(db: Session, utente_id: int) -> SchedaArtigiano:
    """La scheda dell'artigiano: account, profilo e campagne per sezioni.

    Sezioni (ADR-53): ``da_approvare`` con le stesse righe di
    ``GET /da-approvare``, ``in_corso`` (attiva, sospesa), ``chiuse`` con le
    ultime tre e il loro totale. ``bozza`` è informativa: la compila e la
    invia l'artigiano.

    Raises:
        NonTrovato: nessun utente con quell'id o non è un artigiano (404).
    """
    record = accesso.utente(db, utente_id)
    if record.ruolo != "artigiano":
        raise NonTrovato("Artigiano non trovato.")
    profilo = artigiani.profilo_di(db, record.id)
    tutte = campagne.campagne_di(db, profilo.id) if profilo is not None else []
    da_approvare = [
        _riga_da_approvare(db, campagna)
        for campagna in tutte
        if campagna.stato in _STATI_DA_APPROVARE
    ]
    da_approvare.sort(key=lambda riga: riga.entro_quando)
    chiuse = [campagna for campagna in tutte if campagna.stato in _STATI_CHIUSE]
    bozze = [campagna for campagna in tutte if campagna.stato == "bozza"]
    return SchedaArtigiano(
        artigiano=UtenteArtigiano(
            id=record.id,
            email=record.email,
            nome=record.nome,
            attivo=record.attivo,
        ),
        profilo=(
            ProfiloArtigiano.model_validate(profilo) if profilo is not None else None
        ),
        canali_collegati=(
            artigiani.canali_collegati(db, profilo.id) if profilo is not None else []
        ),
        bozza=_sezione(db, bozze[0]) if bozze else None,
        da_approvare=da_approvare,
        in_corso=[
            _sezione(db, campagna)
            for campagna in tutte
            if campagna.stato in _STATI_IN_CORSO
        ],
        chiuse=[_sezione(db, campagna) for campagna in chiuse[:_CHIUSE_IN_SCHEDA]],
        totale_chiuse=len(chiuse),
    )
