"""Interventi dell'operatore sul post: quali sono ammessi e il testo (spec §3, R-16, R-30)."""

from dataclasses import replace
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.ai import PostAI, ottieni_ai
from app.core.config import leggi_impostazioni
from app.core.errori import DatiNonValidi, StatoNonValido
from app.moduli.campagne import service as campagne

from .domain import (
    APPROVATO,
    CAMBIA_FOTO,
    DA_APPROVARE,
    IMMAGINE_AI,
    INTERVENTI,
    INTERVENTI_AMMESSI,
    MODIFICA,
    RIGENERA,
    SCHEDE_CANALE,
    STATI_CHE_USANO_LA_FOTO,
    TIPI_INTERVENTO_IN_CORSO,
)
from .generazione import (
    RISCRITTURE,
    _campagna_ai,
    _foto_ai,
    _gruppo_dell_uscita,
    _snapshot,
)
from .immagini_ai import IMMAGINE_NON_CREATA, con_dicitura, descrizione_immagine
from .models import Post, Uscita, VersionePost, VersionePostFoto
from .service import (
    _azzera_spunta,
    _intervento_attivo,
    _post,
    registra_chiamata_ai,
)
from .validatore import BLOCCO, testo_salvabile, valida_testo

# R-03: al massimo 3 rigenerazioni del testo per post (da zero e da proposta insieme).
MAX_RIGENERAZIONI = 3
RIGENERAZIONI = ("rigenera_totale", "rigenera_da_proposta")


def interventi_ammessi(post: Post, stato_campagna: str, adesso: datetime) -> list[str]:
    """Gli interventi che l'operatore può fare adesso sul post (spec R-16).

    Parte da ``INTERVENTI_AMMESSI`` per (stato della campagna, stato del post) e
    toglie ciò che il singolo post non permette: nessun intervento con uno in
    corso (R-31) né su un ``approvato`` che esce entro il margine; senza
    versione corrente non si modifica, rigenera o cambia foto; un'immagine AI
    non cambia foto; a cicli finiti non si rigenera (R-03). Ordine di ``INTERVENTI``.
    """
    ammessi = set(INTERVENTI_AMMESSI.get((stato_campagna, post.stato), ()))
    if not ammessi or _intervento_attivo(post, adesso):
        return []
    margine = timedelta(minutes=leggi_impostazioni().margine_slot_minuti)
    if post.stato == APPROVATO and post.data_ora < adesso + margine:
        return []
    if post.versione_corrente is None:
        ammessi -= {MODIFICA, RIGENERA, CAMBIA_FOTO}
    if post.riempitivo is not None:
        ammessi -= {CAMBIA_FOTO}
    if post.n_rigenerazioni_testo >= MAX_RIGENERAZIONI:
        ammessi -= {RIGENERA}
    return [uno for uno in INTERVENTI if uno in ammessi]


def verifica_intervento(
    db: Session, post: Post, intervento: str, adesso: datetime
) -> "campagne.Campagna":
    """Restituisce la campagna se l'intervento è ammesso sul post, altrimenti 409.

    Il messaggio dice il primo motivo che vale, tra quelli che riguardano un
    intervento che lo stato di campagna e post permetterebbe (brief-interventi §1.1).

    Raises:
        NonTrovato: la campagna del post non esiste.
        StatoNonValido: l'intervento non è ammesso (409).
    """
    campagna = campagne.campagna(db, post.campagna_id)
    if intervento in interventi_ammessi(post, campagna.stato, adesso):
        return campagna
    previsti = INTERVENTI_AMMESSI.get((campagna.stato, post.stato), frozenset())
    margine = leggi_impostazioni().margine_slot_minuti
    if intervento in previsti:
        if _intervento_attivo(post, adesso):
            raise StatoNonValido("Sul post c'è un intervento in corso.")
        if post.stato == APPROVATO and post.data_ora < adesso + timedelta(
            minutes=margine
        ):
            raise StatoNonValido(
                f"Il post esce tra meno di {margine} minuti: non si tocca più."
            )
        if intervento == CAMBIA_FOTO and post.riempitivo is not None:
            raise StatoNonValido("Un post con un'immagine AI non cambia foto.")
        if intervento == RIGENERA and post.n_rigenerazioni_testo >= MAX_RIGENERAZIONI:
            raise StatoNonValido(
                "Le 3 rigenerazioni del testo sono finite: resta la modifica a mano."
            )
        if post.versione_corrente is None:
            raise StatoNonValido("Il post non ha ancora un testo.")
    raise StatoNonValido(
        f"Questo intervento non è ammesso: la campagna è «{campagna.stato}», "
        f"il post è «{post.stato}»."
    )


def _foto_della_versione(post: Post) -> set[int]:
    corrente = post.versione_corrente
    return {legame.foto_id for legame in corrente.legami_foto} if corrente else set()


def foto_possibili(db: Session, post_id: int, adesso: datetime) -> list:
    """Le foto con cui si può cambiare quella del post, la migliore in cima (R-36).

    Sono le foto ``caricata`` del gruppo dell'uscita, idonee per l'analisi
    oppure senza analisi perché arrivate con una richiesta all'artigiano (R-46),
    che non sono nella versione corrente del post né in quella di un altro post
    della campagna sullo stesso canale ancora vivo (costituzione §1.9). Prima
    quelle senza analisi, poi per punteggio decrescente, poi per id.

    Raises:
        NonTrovato: il post non esiste.
        StatoNonValido: ``cambia_foto`` non è ammesso sul post, o il post non ha
            un gruppo di foto perché ha un'immagine AI (409).
    """
    record = _post(db, post_id)
    campagna = verifica_intervento(db, record, CAMBIA_FOTO, adesso)
    uscita = db.get(Uscita, record.uscita_id)
    if uscita is None or uscita.gruppo_id is None:
        raise StatoNonValido("Un post con un'immagine AI non cambia foto.")
    occupate = _foto_della_versione(record)
    altri = db.scalars(
        select(Post).where(
            Post.campagna_id == campagna.id,
            Post.canale == record.canale,
            Post.id != record.id,
            Post.stato.in_(STATI_CHE_USANO_LA_FOTO),
        )
    )
    for altro in altri:
        occupate |= _foto_della_versione(altro)
    gruppo = next(
        (
            g
            for g in campagne.gruppi_della_campagna(db, campagna.id)
            if g.id == uscita.gruppo_id
        ),
        None,
    )
    candidate = [
        una
        for una in (gruppo.foto if gruppo is not None else [])
        if una.origine == "caricata"
        and una.id not in occupate
        and (not una.analisi_ai or una.analisi_ai.get("idonea") is True)
    ]

    def punteggio(una) -> float:
        return float((una.analisi_ai or {}).get("punteggio") or 0)

    return sorted(
        candidate,
        key=lambda una: (bool(una.analisi_ai), -punteggio(una), una.id),
    )


def cambia_foto(
    db: Session, post_id: int, foto_id: int, utente_id: int, adesso: datetime
) -> VersionePost:
    """Una versione ``cambio_foto``: stesso testo, un'altra foto (R-36, CA-71).

    La foto scelta prende il posto di quella nella posizione più bassa; le altre
    posizioni (caroselli, congelati) si copiano. Testo, hashtag ed errori del
    validatore restano quelli della versione corrente; la spunta cade, non
    nascono cicli (R-03) e ``da_rivedere`` non cambia.

    Raises:
        NonTrovato: il post non esiste.
        StatoNonValido: ``cambia_foto`` non è ammesso sul post (409).
        DatiNonValidi: la foto non è tra ``foto_possibili()`` (422).
    """
    record = _post(db, post_id)
    possibili = foto_possibili(db, post_id, adesso)
    scelta = next((una for una in possibili if una.id == foto_id), None)
    if scelta is None:
        raise DatiNonValidi(
            "Questa foto non si può usare per il post: deve essere del gruppo "
            "dell'uscita, idonea o arrivata con una richiesta, e non già su questo canale."
        )
    corrente = record.versione_corrente
    nuova = VersionePost(
        post_id=record.id,
        numero=corrente.numero + 1,
        testo=corrente.testo,
        hashtag=list(corrente.hashtag),
        autore_id=utente_id,
        tipo_intervento="cambio_foto",
        errori_validazione=[dict(e) for e in corrente.errori_validazione or []],
    )
    db.add(nuova)
    db.flush()
    sostituita = min(legame.posizione for legame in corrente.legami_foto)
    for legame in corrente.legami_foto:
        db.add(
            VersionePostFoto(
                versione_id=nuova.id,
                posizione=legame.posizione,
                foto_id=scelta.id if legame.posizione == sostituita else legame.foto_id,
            )
        )
    campagne.aggiorna_foto(db, scelta.id, scelta.analisi_ai, scelta.n_utilizzi + 1)
    _azzera_spunta(record)
    db.flush()
    db.expire(record, ["versioni"])
    db.expire(nuova, ["legami_foto"])
    return nuova


def _pulisci_hashtag(hashtag: list[str]) -> list[str]:
    """Gli hashtag come li salva l'AI: senza ``#``, senza spazi, senza voci vuote."""
    puliti = (uno.strip().lstrip("#").strip() for uno in hashtag)
    return [uno for uno in puliti if uno]


def modifica(
    db: Session,
    post_id: int,
    utente_id: int,
    testo: str,
    hashtag: list[str],
    adesso: datetime,
) -> VersionePost:
    """La modifica a mano come nuova versione ``modifica_operatore`` (R-30, CA-64, CA-84).

    Ammessa dove ``interventi_ammessi()`` la dà: in revisione e, entro i
    limiti di R-16, dopo l'approvazione (409 negli altri casi). La versione ha lo stesso gruppo di foto della corrente e passa dal
    validatore (R-09): con un blocco, o con testo e hashtag uguali a quelli
    correnti, non si salva niente. Non conta cicli (R-03), azzera la spunta e,
    non avendo blocchi, toglie a un post ``da_rivedere`` il suo indicatore.
    Gli avvisi si salvano con la versione e non fermano nulla.
    """
    record = _post(db, post_id)
    campagna = verifica_intervento(db, record, MODIFICA, adesso)
    corrente = record.versione_corrente

    testo = testo.strip()
    hashtag = _pulisci_hashtag(hashtag)
    if testo == corrente.testo.strip() and hashtag == list(corrente.hashtag):
        raise DatiNonValidi("Il testo e gli hashtag sono uguali a quelli di prima.")
    snapshot = campagna.profilo_snapshot
    errori = [
        dict(errore)
        for errore in valida_testo(
            testo,
            hashtag,
            record.canale,
            snapshot if isinstance(snapshot, dict) else {},
        )
    ]
    blocchi = [errore["messaggio"] for errore in errori if errore["livello"] == BLOCCO]
    if blocchi:
        raise DatiNonValidi(" ".join(blocchi))

    nuova = VersionePost(
        post_id=record.id,
        numero=corrente.numero + 1,
        testo=testo,
        hashtag=hashtag,
        autore_id=utente_id,
        tipo_intervento="modifica_operatore",
        errori_validazione=errori,
    )
    db.add(nuova)
    db.flush()
    for legame in corrente.legami_foto:
        db.add(
            VersionePostFoto(
                versione_id=nuova.id,
                posizione=legame.posizione,
                foto_id=legame.foto_id,
            )
        )
    record.da_rivedere = False
    _azzera_spunta(record)
    db.flush()
    db.expire(record, ["versioni"])
    db.expire(nuova, ["legami_foto"])
    return nuova


def puo_rigenerare(db: Session, post_id: int, adesso: datetime) -> bool:
    """Vero se si può chiedere una rigenerazione del testo (R-03, R-31)."""
    record = _post(db, post_id)
    campagna = campagne.campagna(db, record.campagna_id)
    return RIGENERA in interventi_ammessi(record, campagna.stato, adesso)


def accendi_intervento(db: Session, post_id: int, tipo: str, adesso: datetime) -> Post:
    """Segna sul post l'intervento in corso: il tipo e l'ora di partenza (R-31)."""
    if tipo not in TIPI_INTERVENTO_IN_CORSO:
        raise DatiNonValidi("Tipo di intervento non valido.")
    record = _post(db, post_id)
    campagna = campagne.campagna(db, record.campagna_id)
    if tipo in RIGENERAZIONI:
        if not puo_rigenerare(db, post_id, adesso):
            raise StatoNonValido(
                "Il post non si può rigenerare: campagna non in revisione, post non "
                "da approvare, intervento già in corso o 3 rigenerazioni già fatte."
            )
    elif not (
        campagna.stato == "in_revisione"
        and record.stato == DA_APPROVARE
        and not _intervento_attivo(record, adesso)
    ):
        raise StatoNonValido("Il post non si può modificare adesso.")
    record.intervento_in_corso = tipo
    record.intervento_dal = adesso
    db.flush()
    return record


def spegni_intervento(db: Session, post_id: int) -> None:
    """Toglie l'intervento in corso senza toccare la versione né i cicli (R-31)."""
    record = db.get(Post, post_id)
    if record is not None:
        record.intervento_in_corso = None
        record.intervento_dal = None
        db.flush()


def rigenera(
    db: Session,
    post_id: int,
    testo_proposto: str | None,
    nota: str | None,
    adesso: datetime,
) -> VersionePost | None:
    """Una esecuzione di ``rigenera_post``: nuovo testo, stesse foto (R-03, R-04, R-31).

    Non fa nulla (``None``) se la campagna non è ``in_revisione``, il post non è
    ``da_approvare`` o non ha un intervento di rigenerazione in corso. Il tipo
    della versione (``rigenera_totale`` o ``rigenera_da_proposta``) è quello
    dell'intervento. L'AI riceve i testi delle versioni già scritte come «cosa
    non rifare»; il testo passa dal validatore con le stesse riscritture della
    generazione (R-09), e con un blocco che resta il post è ``da_rivedere``.
    Il ciclo si conta quando nasce la versione, e in quel momento l'intervento
    si spegne e la spunta cade. Un errore lascia tutto com'è: lo gestisce il job.

    Raises:
        DatiNonValidi: ``rigenera_da_proposta`` senza testo proposto.
        ErroreAI: errore tecnico del provider (R-35).
    """
    record = db.get(Post, post_id)
    if record is None or record.intervento_in_corso not in RIGENERAZIONI:
        return None
    campagna = campagne.campagna(db, record.campagna_id)
    if campagna.stato != "in_revisione" or record.stato != DA_APPROVARE:
        return None
    corrente = record.versione_corrente
    if corrente is None:
        return None
    tipo = record.intervento_in_corso
    proposto = (testo_proposto or "").strip() or None
    if tipo == "rigenera_da_proposta" and proposto is None:
        raise DatiNonValidi("Per rigenerare da un testo serve il testo proposto.")
    if tipo == "rigenera_totale":
        proposto = None
    nota = (nota or "").strip() or None

    uscita = db.get(Uscita, record.uscita_id)
    per_id = {
        una.id: una
        for una in campagne.foto_per_id(db, [l.foto_id for l in corrente.legami_foto])
    }
    foto = [per_id[l.foto_id] for l in corrente.legami_foto if l.foto_id in per_id]
    gruppo = _gruppo_dell_uscita(db, campagna, uscita)
    da_scrivere = PostAI(
        canale=record.canale,
        tema=uscita.tema,
        formato=record.formato,
        data_ora=record.data_ora,
        riempitivo=record.riempitivo,
        descrizione_gruppo=gruppo.descrizione if gruppo is not None else None,
        # Come in generazione: il testo di un'immagine AI si chiede dal tema.
        foto=[]
        if record.riempitivo == IMMAGINE_AI
        else [_foto_ai(una) for una in foto],
        immagine_ai=(
            descrizione_immagine(campagna, record, uscita.tema)
            if record.riempitivo == IMMAGINE_AI and foto
            else None
        ),
    )
    dicitura = record.riempitivo == IMMAGINE_AI and bool(foto)
    rifiutate = [v.testo for v in record.versioni if v.testo.strip()]
    snapshot = _snapshot(campagna)
    ai = ottieni_ai()
    precedente, errori = None, None
    for _ in range(1 + RISCRITTURE):
        scritto = ai.genera_post(
            snapshot,
            _campagna_ai(campagna),
            da_scrivere,
            SCHEDE_CANALE[record.canale],
            testo_precedente=precedente,
            violazioni=errori,
            versioni_rifiutate=rifiutate,
            testo_proposto=proposto,
            nota=nota,
        )
        # Come in generazione: un carattere nullo nella risposta non si salva.
        scritto = replace(
            scritto,
            testo=testo_salvabile(scritto.testo),
            hashtag=[testo_salvabile(uno) for uno in scritto.hashtag],
        )
        registra_chiamata_ai(db, campagna.id, ai.ultimo_uso, post_id=record.id)
        scritto_dall_ai = scritto.testo
        if dicitura:
            scritto = replace(scritto, testo=con_dicitura(scritto.testo))
        errori = valida_testo(scritto.testo, scritto.hashtag, record.canale, snapshot)
        if not errori:
            break
        precedente = scritto_dall_ai
    errori = [dict(errore) for errore in errori]
    # Il testo nuovo non crea l'immagine che manca: il blocco resta.
    errori = [
        dict(vecchio)
        for vecchio in corrente.errori_validazione or []
        if vecchio["regola"] == IMMAGINE_NON_CREATA
    ] + errori

    nuova = VersionePost(
        post_id=record.id,
        numero=corrente.numero + 1,
        testo=scritto.testo,
        hashtag=list(scritto.hashtag),
        autore_id=None,
        tipo_intervento=tipo,
        testo_proposto=proposto,
        nota=nota,
        provider_ai=scritto.provider,
        modello_ai=scritto.modello,
        versione_prompt=scritto.versione_prompt,
        errori_validazione=errori,
    )
    db.add(nuova)
    db.flush()
    for legame in corrente.legami_foto:
        db.add(
            VersionePostFoto(
                versione_id=nuova.id,
                posizione=legame.posizione,
                foto_id=legame.foto_id,
            )
        )
    record.n_rigenerazioni_testo += 1
    record.da_rivedere = any(errore["livello"] == BLOCCO for errore in errori)
    record.intervento_in_corso = None
    record.intervento_dal = None
    _azzera_spunta(record)
    db.flush()
    db.expire(record, ["versioni"])
    db.expire(nuova, ["legami_foto"])
    return nuova
