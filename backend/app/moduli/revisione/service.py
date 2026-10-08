"""Logica del modulo revisione: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.coda import GENERA_CAMPAGNA, accoda
from app.core.errori import StatoNonValido
from app.moduli.accesso import service as accesso
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti

from .models import Approvazione
from .schemas import (
    CampagnaSchema,
    ErroreSchema,
    FotoLegataSchema,
    FotoNonUsataSchema,
    GruppoFotoNonUsateSchema,
    GruppoSchema,
    PianoSchema,
    PostSchema,
    UscitaSchema,
    VediCampagnaSchema,
    VersionePostSchema,
)


def _versione(versione) -> VersionePostSchema:
    return VersionePostSchema(
        id=versione.id,
        numero=versione.numero,
        testo=versione.testo,
        hashtag=list(versione.hashtag),
        autore_id=versione.autore_id,
        tipo_intervento=versione.tipo_intervento,
        testo_proposto=versione.testo_proposto,
        nota=versione.nota,
        provider_ai=versione.provider_ai,
        modello_ai=versione.modello_ai,
        versione_prompt=versione.versione_prompt,
        errori_validazione=versione.errori_validazione,
        creata_il=versione.creata_il,
        foto=[
            FotoLegataSchema(foto_id=legame.foto_id, posizione=legame.posizione)
            for legame in versione.legami_foto
        ],
    )


def _post(post) -> PostSchema:
    corrente = post.versione_corrente
    return PostSchema(
        post_id=post.id,
        canale=post.canale,
        formato=post.formato,
        riempitivo=post.riempitivo,
        data_ora=post.data_ora,
        stato=post.stato,
        da_rivedere=post.da_rivedere,
        controllato_da=post.controllato_da,
        controllato_il=post.controllato_il,
        intervento_in_corso=post.intervento_in_corso,
        intervento_dal=post.intervento_dal,
        versione_corrente=_versione(corrente) if corrente is not None else None,
        versioni=[_versione(v) for v in post.versioni],
    )


def vedi_campagna(
    db: Session, campagna_id: int, stato: str | None = None
) -> VediCampagnaSchema:
    """Tutto ciò che serve alla pagina Vedi campagna (plan §3, spec §2.3).

    In ogni stato dopo l'invio: la campagna, il piano corrente se c'è, le
    uscite con i post dei canali, le foto che il piano non usa con il motivo
    e l'ultimo errore della generazione. Con ``stato`` i post si filtrano;
    piano, uscite, foto ed errore restano quelli della campagna intera.
    """
    record = campagne.campagna(db, campagna_id)
    post = contenuti.post_della_campagna(db, campagna_id)
    usate = {
        legame.foto_id
        for uno in post
        for versione in uno.versioni
        for legame in versione.legami_foto
    }
    if stato is not None:
        post = [uno for uno in post if uno.stato == stato]
    per_uscita = {}
    for uno in post:
        per_uscita.setdefault(uno.uscita_id, []).append(uno)

    gruppi = {g.id: g for g in campagne.gruppi_della_campagna(db, campagna_id)}
    uscite = [
        UscitaSchema(
            id=uscita.id,
            numero=uscita.numero,
            tema=uscita.tema,
            gruppo=(
                GruppoSchema.model_validate(gruppi[uscita.gruppo_id])
                if uscita.gruppo_id in gruppi
                else None
            ),
            post=[_post(uno) for uno in per_uscita.get(uscita.id, [])],
        )
        for uscita in contenuti.uscite_della_campagna(db, campagna_id)
    ]

    non_usate: dict[int | None, list[FotoNonUsataSchema]] = {}
    for foto in campagne.foto_della_campagna(db, campagna_id):
        if foto.id in usate:
            continue
        motivo = (foto.analisi_ai or {}).get("motivo")
        non_usate.setdefault(foto.gruppo_id, []).append(
            FotoNonUsataSchema(foto_id=foto.id, motivo=motivo)
        )
    foto_non_usate = [
        GruppoFotoNonUsateSchema(
            gruppo_id=gruppo_id,
            descrizione=(
                gruppi[gruppo_id].descrizione if gruppo_id in gruppi else None
            ),
            foto=foto,
        )
        for gruppo_id, foto in non_usate.items()
    ]

    piano = contenuti.piano_corrente(db, campagna_id)
    errore = contenuti.ultimo_errore(db, campagna_id)
    return VediCampagnaSchema(
        campagna=CampagnaSchema.model_validate(record),
        piano=PianoSchema.model_validate(piano) if piano is not None else None,
        uscite=uscite,
        foto_non_usate=foto_non_usate,
        ultimo_errore=(
            ErroreSchema.model_validate(errore) if errore is not None else None
        ),
    )


def approva(
    db: Session, campagna_id: int, utente: accesso.Utente, adesso: datetime
) -> None:
    """Approva in blocco una campagna in revisione (R-14, CA-21).

    I post ``da_approvare`` diventano ``approvato``; quelli con la data già
    passata diventano ``scaduto``; ``scartato`` e ``scaduto`` restano. Ogni
    versione approvata ha la sua riga in ``approvazione`` e la campagna una
    decisione ``approvata`` prima di passare ad ``attiva``.

    Raises:
        StatoNonValido: campagna non in revisione, post da rivedere o con un
            intervento in corso, nessun post da approvare (409, CA-22).
    """
    record = campagne.campagna(db, campagna_id)
    if record.stato != "in_revisione":
        raise StatoNonValido("La campagna non è in revisione.")
    for versione in contenuti.approva_post(db, campagna_id, adesso):
        db.add(
            Approvazione(
                versione_id=versione.id,
                utente_id=utente.id,
                ruolo=utente.ruolo,
                esito="approvato",
            )
        )
    campagne.registra_decisione(
        db, record, utente.id, "approvata", motivo=None, nota=None, foto_segnate=[]
    )
    campagne.cambia_stato(db, record, "attiva", ora=adesso)


def prosegui(db: Session, campagna_id: int, utente: accesso.Utente) -> None:
    """Fa ripartire la generazione da un piano debole (spec §2.3, R-20).

    ``piano_da_rivedere`` torna ``in_generazione``, la decisione
    ``proseguita`` si registra e il job ``genera_campagna`` riprende
    dai testi. Senza post nel piano o senza nessuna foto disponibile
    la campagna resta ferma (409).
    """
    record = campagne.campagna(db, campagna_id)
    if record.stato != "piano_da_rivedere":
        raise StatoNonValido("La campagna non è ferma su un piano da rivedere.")
    if not contenuti.post_della_campagna(db, campagna_id):
        raise StatoNonValido("Il piano non contiene post: impossibile proseguire.")
    disponibili = [
        foto
        for foto in campagne.foto_della_campagna(db, campagna_id)
        if (foto.analisi_ai or {}).get("idonea")
        and not (foto.analisi_ai or {}).get("simile_a")
    ]
    if not disponibili:
        raise StatoNonValido("Nessuna foto disponibile: la campagna resta ferma.")
    campagne.registra_decisione(
        db,
        record,
        utente.id,
        "proseguita",
        motivo=None,
        nota=None,
        foto_segnate=[],
    )
    campagne.cambia_stato(db, record, "in_generazione")
    accoda(GENERA_CAMPAGNA, campagna_id=record.id)
