"""Logica del modulo revisione: l'unica parte che gli altri moduli possono importare."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.errori import DatiNonValidi, StatoNonValido
from app.core.orologio import adesso as ora_adesso
from app.moduli.accesso import service as accesso
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import service as contenuti

from . import scadenze as scadenze_modulo
from .models import Approvazione
from .schemas import (
    CampagnaSchema,
    ErroreSchema,
    FotoPrivacySchema,
    FotoLegataSchema,
    FotoNonUsataSchema,
    GruppoFotoNonUsateSchema,
    GruppoSchema,
    PianoSchema,
    PostSchema,
    PrivacyDaDecidereSchema,
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


def _post(db, post, stato_campagna: str, adesso: datetime) -> PostSchema:
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
        interventi=contenuti.interventi_ammessi(post, stato_campagna, adesso),
        foto=contenuti.vista_foto(db, post),
    )


def vedi_campagna(
    db: Session,
    campagna_id: int,
    stato: str | None = None,
    adesso: datetime | None = None,
) -> VediCampagnaSchema:
    """Tutto ciò che serve alla pagina Vedi campagna (plan §3, spec §2.3).

    In ogni stato dopo l'invio: la campagna, il piano corrente se c'è, le
    uscite con i post dei canali, le foto che il piano non usa con il motivo
    e l'ultimo errore della generazione. Con ``stato`` i post si filtrano;
    piano, uscite, foto ed errore restano quelli della campagna intera. Ogni
    post dice gli ``interventi`` che l'operatore può fare ``adesso`` (R-16);
    senza ``adesso`` vale l'ora di ``core.orologio``.
    """
    if adesso is None:
        adesso = ora_adesso()
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
            post=[
                _post(db, uno, record.stato, adesso)
                for uno in per_uscita.get(uscita.id, [])
            ],
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
        costo_ai=contenuti.costo_ai_della_campagna(db, campagna_id),
        privacy_da_decidere=_riepilogo_privacy(
            contenuti.privacy_da_decidere(db, campagna_id)
        ),
    )


def _riepilogo_privacy(voci: list[dict]) -> PrivacyDaDecidereSchema:
    return PrivacyDaDecidereSchema(
        foto=len(voci),
        zone=sum(v["zone"] for v in voci),
        minori=sum(v["minori"] for v in voci),
        dettaglio=[FotoPrivacySchema(**v) for v in voci],
    )


def anteprima_foto(
    db: Session, post_id: int, variante: str | None, utente: accesso.Utente
) -> bytes:
    """Il JPEG della foto del post come esce (RT-08): per l'operatore la variante chiesta, per l'artigiano il render approvato."""
    return contenuti.anteprima_foto(db, post_id, variante, utente.ruolo, utente.id)


def approva(
    db: Session,
    campagna_id: int,
    utente: accesso.Utente,
    adesso: datetime,
    conferma_privacy: bool = False,
    oscura_tutte: bool = False,
) -> None:
    """Approva in blocco una campagna in revisione (R-14, CA-21).

    I post ``da_approvare`` diventano ``approvato``; quelli con la data già
    passata diventano ``scaduto``; ``scartato`` e ``scaduto`` restano. Ogni
    versione approvata ha la sua riga in ``approvazione`` e la campagna una
    decisione ``approvata`` prima di passare ad ``attiva``.

    Con zone di privacy ancora da decidere (RT-29) serve ``conferma_privacy`` (restano
    spente) oppure ``oscura_tutte`` (si accendono tutte, con una versione ``ritocco_foto``
    per ogni foto, nella stessa transazione): altrimenti 422 con il riepilogo.

    Raises:
        StatoNonValido: campagna non in revisione, post da rivedere o con un
            intervento in corso, nessun post da approvare (409, CA-22).
        DatiNonValidi: ci sono zone di privacy da decidere e manca la conferma (422).
    """
    record = campagne.campagna_bloccata(db, campagna_id)
    if record.stato != "in_revisione":
        raise StatoNonValido("La campagna non è in revisione.")
    da_decidere = contenuti.privacy_da_decidere(db, campagna_id)
    if da_decidere and not (conferma_privacy or oscura_tutte):
        riepilogo = _riepilogo_privacy(da_decidere)
        raise DatiNonValidi(
            f"Ci sono {riepilogo.foto} foto con {riepilogo.zone} zone di privacy da "
            "decidere: conferma che restano come sono oppure oscurale tutte."
        )
    if oscura_tutte:
        for voce in da_decidere:
            contenuti.ritocca_foto(
                db, voce["post_ids"][0], None, True, utente.id, adesso
            )
    for versione in contenuti.approva_post(db, campagna_id, adesso):
        db.add(
            Approvazione(
                versione_id=versione.id,
                utente_id=utente.id,
                ruolo=utente.ruolo,
                esito="approvato",
            )
        )
    contenuti.rendi_foto_approvate(db, campagna_id)
    campagne.registra_decisione(
        db, record, utente.id, "approvata", motivo=None, nota=None, foto_segnate=[]
    )
    campagne.cambia_stato(db, record, "attiva", ora=adesso)


def scadenze(db: Session, adesso: datetime) -> None:
    """Applica le scadenze morbide e ferma le campagne bloccate (R-06, R-35).

    Chiamata dal tick, ogni minuto, prima di ``pubblica_dovuti()``
    (``worker.py``). Tre cose, tutte idempotenti: i post ``da_approvare`` con
    la data passata diventano ``scaduto``; la campagna con un piano diventa
    ``scaduta`` quando i ``da_approvare`` sono meno della metà dei post chiesti
    sui canali non tolti, e senza piano alle 00:00 (Europe/Rome) del giorno
    d'inizio, con la notifica ``campagna_scaduta`` all'artigiano; una campagna
    ferma da 30 minuti in ``inviata`` o ``in_generazione`` va in
    ``generazione_fallita`` con ``contenuti.ferma_generazione()``. Due tick di
    seguito con lo stesso ``adesso``: il secondo non cambia nulla.
    """
    scadenze_modulo.scadenze(db, adesso)
