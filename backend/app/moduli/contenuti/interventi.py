"""Interventi dell'operatore sul post: quali sono ammessi e il testo (spec §3, R-16, R-30)."""

from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any, NamedTuple

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
    MAX_RIGENERAZIONI_IMMAGINE,
    MODIFICA,
    RIGENERA,
    RIGENERA_IMMAGINE,
    SCHEDE_CANALE,
    STATI_CHE_USANO_LA_FOTO,
    TIPI_INTERVENTO_IN_CORSO,
)
from .generazione import (
    RISCRITTURE,
    attacchi_degli_altri_post,
    _campagna_ai,
    _foto_ai,
    _gruppo_dell_uscita,
    _snapshot,
)
from .immagini_ai import (
    IMMAGINE_NON_CREATA,
    con_dicitura,
    descrizione_immagine,
    immagine_rigenerata,
    senza_dicitura,
)
from .models import Post, Uscita, VersionePost, VersionePostFoto
from .service import (
    _azzera_spunta,
    _intervento_attivo,
    _post,
    contesto_chiamata_ai,
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
        ammessi -= {MODIFICA, RIGENERA, RIGENERA_IMMAGINE, CAMBIA_FOTO}
    if post.n_rigenerazioni_testo >= MAX_RIGENERAZIONI:
        ammessi -= {RIGENERA}
    if _rigenerazioni_immagine(post) >= MAX_RIGENERAZIONI_IMMAGINE:
        ammessi -= {RIGENERA_IMMAGINE}
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
        if intervento == RIGENERA and post.n_rigenerazioni_testo >= MAX_RIGENERAZIONI:
            raise StatoNonValido(
                "Le 3 rigenerazioni del testo sono finite: resta la modifica a mano."
            )
        if (
            intervento == RIGENERA_IMMAGINE
            and _rigenerazioni_immagine(post) >= MAX_RIGENERAZIONI_IMMAGINE
        ):
            raise StatoNonValido(
                "Questa immagine è già stata rigenerata 3 volte: scegli una foto "
                "con Cambia immagine."
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


def _rigenerazioni_immagine(post: Post) -> int:
    """Quante versioni ``rigenera_immagine`` ha già il post (R-49)."""
    return sum(1 for una in post.versioni if una.tipo_intervento == RIGENERA_IMMAGINE)


def post_toccati_dall_immagine(db: Session, post: Post) -> list[Post]:
    """I post che una rigenerazione dell'immagine tocca (R-49).

    Se la foto della versione corrente è ``creata_ai`` l'immagine è dell'uscita
    (R-28): valgono tutti i post ``da_approvare`` dell'uscita che usano quella
    foto. Se è una foto vera, o il post non ne ha una (il blocco
    ``immagine_non_creata``), vale solo quel post.
    """
    corrente = post.versione_corrente
    if corrente is None or not corrente.legami_foto:
        return [post]
    foto_id = corrente.legami_foto[0].foto_id
    foto = campagne.foto_per_id(db, [foto_id])
    if not foto or foto[0].origine != "creata_ai":
        return [post]
    altri = db.scalars(
        select(Post)
        .where(Post.uscita_id == post.uscita_id, Post.stato == DA_APPROVARE)
        .order_by(Post.id)
    )
    toccati = [
        uno
        for uno in altri
        if uno.id == post.id
        or (
            uno.versione_corrente is not None
            and any(
                legame.foto_id == foto_id
                for legame in uno.versione_corrente.legami_foto
            )
        )
    ]
    return toccati or [post]


def _prompt_delle_immagini_gia_avute(db: Session, toccati: list[Post]) -> list[str]:
    """I prompt delle immagini che l'uscita ha già avuto, da non ripetere (R-49)."""
    ids = {
        legame.foto_id
        for uno in toccati
        for versione in uno.versioni
        for legame in versione.legami_foto
    }
    prompts: list[str] = []
    for una in campagne.foto_per_id(db, sorted(ids)):
        analisi = una.analisi_ai or {}
        prompt = analisi.get("prompt")
        if una.origine == "creata_ai" and isinstance(prompt, str):
            prompt = " ".join(prompt.split())
            if prompt and prompt not in prompts:
                prompts.append(prompt)
    return prompts


def accendi_rigenerazione_immagine(
    db: Session,
    post_id: int,
    riscrivi_testo: bool,
    nota_testo: str | None,
    adesso: datetime,
) -> list[Post]:
    """Controlla e accende ``rigenera_immagine`` sui post toccati (R-49, R-31).

    Tutti i controlli vengono prima di cambiare qualcosa: un 409 lascia i post
    come sono. Il limite di 3 vale per ogni post toccato; con ``riscrivi_testo``
    serve anche un ciclo di R-03 rimasto.

    Raises:
        NonTrovato: il post non esiste.
        StatoNonValido: intervento non ammesso, immagine già rigenerata 3 volte,
            un intervento in corso o testo senza cicli (409).
    """
    record = _post(db, post_id)
    verifica_intervento(db, record, RIGENERA_IMMAGINE, adesso)
    toccati = post_toccati_dall_immagine(db, record)
    for uno in toccati:
        if _rigenerazioni_immagine(uno) >= MAX_RIGENERAZIONI_IMMAGINE:
            raise StatoNonValido(
                "Questa immagine è già stata rigenerata 3 volte: scegli una foto "
                "con Cambia immagine."
            )
        if _intervento_attivo(uno, adesso):
            raise StatoNonValido("Sul post c'è un intervento in corso.")
    if riscrivi_testo:
        for uno in toccati:
            if uno.n_rigenerazioni_testo >= MAX_RIGENERAZIONI:
                raise StatoNonValido(
                    "Il testo di questo post non si può più rigenerare: modificalo a mano."
                )
    for uno in toccati:
        uno.intervento_in_corso = RIGENERA_IMMAGINE
        uno.intervento_dal = adesso
    db.flush()
    return toccati


def spegni_rigenerazione_immagine(db: Session, post_id: int) -> None:
    """Spegne ``rigenera_immagine`` sul post e sui post della sua uscita (R-31)."""
    record = db.get(Post, post_id)
    if record is None:
        return
    for uno in post_toccati_dall_immagine(db, record):
        if uno.intervento_in_corso == RIGENERA_IMMAGINE:
            uno.intervento_in_corso = None
            uno.intervento_dal = None
    db.flush()


def rigenera_immagine(
    db: Session,
    post_id: int,
    nota: str | None,
    riscrivi_testo: bool,
    nota_testo: str | None,
    adesso: datetime,
    esecuzione: int | None = None,
) -> list[VersionePost] | None:
    """Una esecuzione di ``rigenera_immagine`` (R-49, CA-102, CA-103).

    Non fa nulla (``None``) se la campagna non è ``in_revisione``, il post non è
    ``da_approvare`` o non c'è l'intervento in corso. Crea una foto ``creata_ai``
    con il prompt e la nota in ``analisi_ai`` e una versione
    ``rigenera_immagine`` con lo stesso testo su ogni post toccato; la foto
    vecchia resta (costituzione §1.2). Con ``riscrivi_testo`` segue, nello
    stesso job, una versione ``rigenera_totale`` che conta un ciclo di R-03.
    Due rifiuti del provider: nessuna versione e intervento spento.
    """
    record = db.get(Post, post_id)
    if record is None or record.intervento_in_corso != RIGENERA_IMMAGINE:
        return None
    campagna = campagne.campagna(db, record.campagna_id)
    if campagna.stato != "in_revisione" or record.stato != DA_APPROVARE:
        return None

    toccati = post_toccati_dall_immagine(db, record)
    uscita = db.get(Uscita, record.uscita_id)
    nota = (nota or "").strip() or None
    esito = immagine_rigenerata(
        db,
        campagna,
        ottieni_ai(),
        record,
        uscita.tema,
        nota,
        _prompt_delle_immagini_gia_avute(db, toccati),
        tentativo=esecuzione,
    )
    if esito.foto is None:
        for uno in toccati:
            if uno.intervento_in_corso == RIGENERA_IMMAGINE:
                uno.intervento_in_corso = None
                uno.intervento_dal = None
        db.flush()
        return None

    snapshot = _snapshot(campagna)
    versioni: list[VersionePost] = []
    for uno in toccati:
        corrente = uno.versione_corrente
        testo = corrente.testo
        if uno.riempitivo != IMMAGINE_AI:
            testo = con_dicitura(testo)
        errori = [
            dict(errore)
            for errore in valida_testo(
                testo, list(corrente.hashtag), uno.canale, snapshot
            )
        ]
        nuova = VersionePost(
            post_id=uno.id,
            numero=corrente.numero + 1,
            testo=testo,
            hashtag=list(corrente.hashtag),
            autore_id=None,
            tipo_intervento=RIGENERA_IMMAGINE,
            nota=nota,
            provider_ai=esito.provider,
            modello_ai=esito.modello,
            versione_prompt=esito.versione_prompt,
            errori_validazione=errori,
        )
        db.add(nuova)
        db.flush()
        if corrente.legami_foto:
            for legame in corrente.legami_foto:
                db.add(
                    VersionePostFoto(
                        versione_id=nuova.id,
                        posizione=legame.posizione,
                        foto_id=esito.foto.id,
                    )
                )
        else:
            # Il post non aveva una foto (blocco `immagine_non_creata`): ora ce l'ha.
            db.add(
                VersionePostFoto(
                    versione_id=nuova.id, posizione=1, foto_id=esito.foto.id
                )
            )
        uno.riempitivo = IMMAGINE_AI
        uno.da_rivedere = any(errore["livello"] == BLOCCO for errore in errori)
        uno.intervento_in_corso = None
        uno.intervento_dal = None
        _azzera_spunta(uno)
        versioni.append(nuova)

    campagne.aggiorna_foto(
        db,
        esito.foto.id,
        esito.foto.analisi_ai,
        (esito.foto.n_utilizzi or 0) + len(toccati),
    )
    db.flush()
    for uno in toccati:
        db.expire(uno, ["versioni"])

    if riscrivi_testo:
        for uno in toccati:
            uno.intervento_in_corso = "rigenera_totale"
            uno.intervento_dal = adesso
        for uno in toccati:
            scritta = rigenera(db, uno.id, None, nota_testo, adesso)
            if scritta is not None:
                versioni.append(scritta)
    return versioni


class FotoPerPost(NamedTuple):
    """Una foto proponibile per Cambia immagine, con da dove viene (R-36)."""

    foto: Any
    provenienza: str  # "gruppo" | "campagna" | "archivio"


def _foto_libere(db: Session, campagna: Any, record: Post) -> set[int]:
    """Le foto già nella versione corrente del post o di un altro post vivo.

    Vale la costituzione §1.9: una foto non esce due volte sullo stesso canale
    nella stessa campagna. Contano i post ancora ``da_approvare``, ``approvato``,
    ``pubblicato`` o ``fallito``.
    """
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
    return occupate


def _proponibile(foto: Any, occupate: set[int]) -> bool:
    """Una foto ``caricata`` idonea (o senza analisi, arrivata con una richiesta)."""
    return (
        foto.origine == "caricata"
        and foto.id not in occupate
        and (not foto.analisi_ai or foto.analisi_ai.get("idonea") is True)
    )


def _ordine(foto: Any) -> tuple[bool, float, int]:
    """L'ordine di oggi: prima senza analisi, poi per punteggio, poi per id."""
    punteggio = float((foto.analisi_ai or {}).get("punteggio") or 0)
    return (bool(foto.analisi_ai), -punteggio, foto.id)


def foto_possibili(db: Session, post_id: int, adesso: datetime) -> list[FotoPerPost]:
    """Le foto con cui si può cambiare quella del post, la migliore in cima (R-36).

    In quest'ordine: (1) le foto del gruppo dell'uscita, (2) le altre foto
    ``caricata`` della campagna, (3) le foto dell'archivio della bottega
    (``campagne.foto_di_archivio()``, R-27). Dentro ogni fonte l'ordine di
    oggi: prima quelle senza analisi (arrivate con una richiesta, R-46), poi
    per punteggio decrescente, poi per id. Restano fuori le foto non idonee e
    quelle già nella versione corrente di un post vivo della campagna sullo
    stesso canale (costituzione §1.9); un id compare una volta sola. Ammessa
    anche sui post con un'immagine AI: in quel caso la prima fonte è vuota.

    Raises:
        NonTrovato: il post non esiste.
        StatoNonValido: ``cambia_foto`` non è ammesso sul post (409).
    """
    record = _post(db, post_id)
    campagna = verifica_intervento(db, record, CAMBIA_FOTO, adesso)
    occupate = _foto_libere(db, campagna, record)
    uscita = db.get(Uscita, record.uscita_id)
    gruppi = campagne.gruppi_della_campagna(db, campagna.id)

    viste: set[int] = set()
    risultato: list[FotoPerPost] = []

    # (1) il gruppo dell'uscita.
    gruppo = None
    if uscita is not None and uscita.gruppo_id is not None:
        gruppo = next((g for g in gruppi if g.id == uscita.gruppo_id), None)
    candidate = [
        una
        for una in (gruppo.foto if gruppo is not None else [])
        if _proponibile(una, occupate)
    ]
    for una in sorted(candidate, key=_ordine):
        risultato.append(FotoPerPost(una, "gruppo"))
        viste.add(una.id)

    # (2) le altre foto della campagna, in qualunque suo gruppo.
    altre = [
        una
        for un_gruppo in gruppi
        for una in un_gruppo.foto
        if una.id not in viste and _proponibile(una, occupate)
    ]
    for una in sorted(altre, key=_ordine):
        if una.id in viste:
            continue
        risultato.append(FotoPerPost(una, "campagna"))
        viste.add(una.id)

    # (3) l'archivio della bottega, così com'è (le non idonee sono già fuori).
    for voce in campagne.foto_di_archivio(
        db, campagna.profilo_id, record.canale, adesso
    ):
        if voce.foto.id in viste or voce.foto.id in occupate:
            continue
        risultato.append(FotoPerPost(voce.foto, "archivio"))
        viste.add(voce.foto.id)

    return risultato


def cambia_foto(
    db: Session,
    post_id: int,
    foto_id: int,
    utente_id: int,
    adesso: datetime,
    riscrivi_testo: bool = False,
) -> VersionePost:
    """Una versione ``cambio_foto``: stesso testo, un'altra foto (R-36, R-49).

    La foto scelta prende il posto di quella nella posizione più bassa; le altre
    posizioni (caroselli, congelati) si copiano. Testo e hashtag restano quelli
    della versione corrente, salvo la dicitura: da un'immagine AI a una foto
    vera il testo perde «Immagine creata con AI» e il post non è più
    ``immagine_ai``. Gli errori del validatore si ricalcolano. La spunta cade,
    non nascono cicli (R-03) e non si tocca l'autore delle versioni vecchie.

    Con ``riscrivi_testo`` (solo in ``in_revisione``) accende l'intervento
    ``rigenera_totale``: il testo lo riscrive il job ``rigenera_post``, con un
    ciclo di R-03. Dopo l'approvazione il testo non si riscrive con l'AI (422).

    Raises:
        NonTrovato: il post non esiste.
        StatoNonValido: ``cambia_foto`` non è ammesso sul post (409), oppure
            ``riscrivi_testo`` senza rigenerazioni del testo rimaste.
        DatiNonValidi: la foto non è tra ``foto_possibili()`` (422), oppure
            ``riscrivi_testo`` dopo l'approvazione.
    """
    record = _post(db, post_id)
    campagna = campagne.campagna(db, record.campagna_id)
    if riscrivi_testo:
        if campagna.stato != "in_revisione":
            raise DatiNonValidi(
                "Dopo l'approvazione il testo non si riscrive con l'AI: "
                "modificalo a mano."
            )
        if record.n_rigenerazioni_testo >= MAX_RIGENERAZIONI:
            raise StatoNonValido(
                "Il testo di questo post non si può più rigenerare: modificalo a mano."
            )
    possibili = foto_possibili(db, post_id, adesso)
    scelta = next((una.foto for una in possibili if una.foto.id == foto_id), None)
    if scelta is None:
        raise DatiNonValidi(
            "Questa foto non si può usare per il post: deve essere del gruppo "
            "dell'uscita, della campagna o dell'archivio, e non già su questo canale."
        )
    corrente = record.versione_corrente
    testo = corrente.testo
    if record.riempitivo == IMMAGINE_AI and scelta.origine != "creata_ai":
        testo = senza_dicitura(testo)
    errori = [
        dict(errore)
        for errore in valida_testo(
            testo, list(corrente.hashtag), record.canale, _snapshot(campagna)
        )
    ]
    nuova = VersionePost(
        post_id=record.id,
        numero=corrente.numero + 1,
        testo=testo,
        hashtag=list(corrente.hashtag),
        autore_id=utente_id,
        tipo_intervento="cambio_foto",
        errori_validazione=errori,
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
    if record.riempitivo == IMMAGINE_AI:
        record.riempitivo = None
    record.da_rivedere = any(errore["livello"] == BLOCCO for errore in errori)
    if riscrivi_testo:
        record.intervento_in_corso = "rigenera_totale"
        record.intervento_dal = adesso
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
    altri = attacchi_degli_altri_post(db, campagna.id, record.canale, record.id)
    for riscrittura in range(1, 2 + RISCRITTURE):
        with contesto_chiamata_ai(
            campagna.id, post_id=record.id, tentativo=riscrittura
        ):
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
                altri_post=altri,
            )
        # Come in generazione: un carattere nullo nella risposta non si salva.
        scritto = replace(
            scritto,
            testo=testo_salvabile(scritto.testo),
            hashtag=[testo_salvabile(uno) for uno in scritto.hashtag],
        )
        registra_chiamata_ai(
            db, campagna.id, ai.ultimo_uso, post_id=record.id, tentativo=riscrittura
        )
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
