"""Generazione di una campagna, a tappe (plan §4, spec §2.2).

Il job chiama ``passo()`` finché c'è lavoro, ogni volta in una transazione
sua. Un passo guarda ciò che è già salvato e fa la prima cosa che manca:

1. avvio: la campagna `inviata` diventa `in_generazione`;
2. analisi: un gruppo di foto caricate non ancora analizzato;
3. piano: all'AI vanno solo le foto migliori per punteggio, fino ai post chiesti
   (R-05); piano dell'AI, controllo, righe `piano`, `uscita`, `post`; i post
   che le foto non coprono sono `immagine_ai` (R-28);
4. testi: un post senza versione, con la sua foto se ne ha una; per un post
   `immagine_ai` l'immagine dell'uscita, creata la prima volta (R-43);
5. fine: la campagna passa `in_revisione`.

Per questo una nuova esecuzione e Riprova riprendono da sole dal punto
giusto (R-24). Se un passo solleva un errore, la sua transazione si
annulla e ``registra_errore()`` decide che cosa succede alla campagna (R-35).
Si usa sempre la fotografia del profilo, mai il profilo corrente (R-11).
"""

import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.ai import (
    AIAdapter,
    CampagnaAI,
    ErroreAI,
    FotoAI,
    GruppoAI,
    PostAI,
    ottieni_ai,
)
from app.core.config import leggi_impostazioni
from app.core.orologio import adesso as ora_di_adesso
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.notifiche import service as notifiche

from . import service
from .domain import DA_APPROVARE, IMMAGINE_AI, SCHEDE_CANALE
from .immagini_ai import (
    blocco_immagine_non_creata,
    con_dicitura,
    descrizione_immagine,
    immagine_del_post,
)
from .models import (
    ErroreGenerazione,
    Piano,
    Post,
    Uscita,
    VersionePost,
    VersionePostFoto,
)
from .piano import controlla_piano, limiti_per_canale
from .validatore import BLOCCO, TESTO_VUOTO, valida_testo

# plan §4: il job gira al massimo 3 volte, a 30 secondi una dall'altra.
ESECUZIONI = 3
ATTESA_SECONDI = 30
# R-09: piano e testo si riscrivono al massimo 3 volte.
RISCRITTURE = 3
# Gli attacchi degli altri post che l'AI riceve (post v3).
ATTACCHI_MAX = 10
ATTACCO_LUNGHEZZA = 120
# Un passo è un gruppo, il piano o un post: molti più passi sono un errore.
MAX_PASSI = 1000

AVVIO = "avvio"
ANALISI = "analisi"
PIANO = "piano"
IMMAGINI = "immagini"
TESTI = "testi"
FINE = "fine"

_CAMPI_ANALISI = (
    "idonea",
    "simile_a",
    "tipo",
    "punteggio",
    "motivo",
    "soggetto",
    "descrizione",
    "persone_riconoscibili",
    "marchi_visibili",
)


class GenerazioneInterrotta(Exception):
    """Errore che ferma l'esecuzione: tipo di R-35, messaggio, tappa e canale."""

    def __init__(
        self, tipo: str, messaggio: str, tappa: str, canale: str | None = None
    ):
        super().__init__(messaggio)
        self.tipo = tipo
        self.messaggio = messaggio
        self.tappa = tappa
        self.canale = canale


@contextmanager
def _nella_tappa(tappa: str, canale: str | None = None) -> Iterator[None]:
    """Un errore dell'AI esce con la tappa e il canale in cui è successo."""
    try:
        yield
    except ErroreAI as errore:
        raise GenerazioneInterrotta(
            errore.tipo, errore.messaggio, tappa, canale
        ) from errore


# --- Che cosa manca -----------------------------------------------------------


def _canali(campagna: Any) -> list[str]:
    """I canali su cui la campagna esce ancora: senza quelli tolti."""
    tolti = set(campagna.canali_tolti or [])
    return [canale for canale in campagna.canali or [] if canale not in tolti]


def _caricate(db: Session, campagna_id: int) -> list[Any]:
    gruppi = campagne.gruppi_della_campagna(db, campagna_id)
    return [gruppo for gruppo in gruppi if gruppo.origine == "caricate"]


def _da_analizzare(db: Session, campagna: Any) -> tuple[Any, list[Any]] | None:
    """Il primo gruppo della campagna con foto senza analisi, insieme a quelle foto."""
    for gruppo in _caricate(db, campagna.id):
        da_fare = [foto for foto in gruppo.foto if foto.analisi_ai is None]
        if da_fare:
            return gruppo, da_fare
    return None


def _post_da_scrivere(db: Session, campagna: Any) -> Post | None:
    """Il primo post ancora senza versione, tra quelli dei canali rimasti."""
    con_versione = select(VersionePost.post_id)
    return db.scalar(
        select(Post)
        .where(
            Post.campagna_id == campagna.id,
            Post.stato == DA_APPROVARE,
            Post.canale.in_(_canali(campagna)),
            Post.id.not_in(con_versione),
        )
        .order_by(Post.data_ora, Post.id)
        .limit(1)
    )


def prossima_tappa(db: Session, campagna: Any) -> str | None:
    """La prima tappa non ancora fatta; `None` se il job non ha nulla da fare."""
    if campagna.stato == "inviata":
        return AVVIO
    if campagna.stato != "in_generazione":
        return None
    if _da_analizzare(db, campagna) is not None:
        return ANALISI
    if service.piano_corrente(db, campagna.id) is None:
        return PIANO
    if _post_da_scrivere(db, campagna) is not None:
        return TESTI
    return FINE


def passo(db: Session, campagna_id: int, adesso: datetime) -> bool:
    """Fa la prima cosa che manca; vero se dopo c'è ancora lavoro.

    Chi chiama apre una transazione per ogni passo: ciò che un passo ha
    salvato resta, anche se quello dopo fallisce (R-24).
    """
    campagna = campagne.campagna(db, campagna_id)
    tappa = prossima_tappa(db, campagna)
    if tappa is None:
        return False
    if tappa == AVVIO:
        campagne.cambia_stato(db, campagna, "in_generazione")
        return True
    if tappa == ANALISI:
        gruppo, da_fare = _da_analizzare(db, campagna)
        _analizza(db, campagna.id, gruppo, da_fare)
        return True
    if tappa == PIANO:
        _pianifica(db, campagna, adesso)
        return True
    if tappa == TESTI:
        _scrivi(db, campagna, _post_da_scrivere(db, campagna))
        return True
    campagne.cambia_stato(db, campagna, "in_revisione")
    notifiche.crea(
        db,
        "campagna_pronta",
        campagna.id,
        adesso,
        contenuto={"titolo": campagna.titolo},
    )
    return False


# --- Analisi ------------------------------------------------------------------


def _foto_ai(foto: Any) -> FotoAI:
    analisi = foto.analisi_ai if isinstance(foto.analisi_ai, dict) else None
    return FotoAI(id=foto.id, file=foto.file, mime=foto.mime, analisi=analisi)


def _gruppo_ai(gruppo: Any, foto: list[Any]) -> GruppoAI:
    return GruppoAI(
        id=gruppo.id,
        descrizione=gruppo.descrizione,
        da_usare_il=gruppo.da_usare_il,
        foto=[_foto_ai(una) for una in foto],
    )


def _non_idonea(motivo: str) -> dict[str, Any]:
    return dict.fromkeys(_CAMPI_ANALISI) | {"idonea": False, "motivo": motivo}


def _analizza(
    db: Session, campagna_id: int, gruppo: Any, senza_analisi: list[Any]
) -> None:
    """Analizza le foto del gruppo che non hanno ancora un'analisi (R-24).

    Un errore `richiesta` o `rifiuto` su una sola foto la rende non idonea,
    con il motivo, e l'analisi continua con le altre (R-35).
    """
    da_fare = list(senza_analisi)
    risultati: dict[int, dict[str, Any]] = {}
    with _nella_tappa(ANALISI):
        ai = ottieni_ai()
        while da_fare:
            try:
                risposta = ai.analizza_gruppo(_gruppo_ai(gruppo, da_fare))
            except ErroreAI as errore:
                ids = {foto.id for foto in da_fare}
                if errore.tipo in ("richiesta", "rifiuto") and errore.foto_id in ids:
                    risultati[errore.foto_id] = _non_idonea(errore.messaggio)
                    da_fare = [f for f in da_fare if f.id != errore.foto_id]
                    continue
                raise
            service.registra_chiamata_ai(db, campagna_id, ai.ultimo_uso)
            for foto in da_fare:
                analisi = risposta.get(foto.id)
                if not isinstance(analisi, dict) or not isinstance(
                    analisi.get("idonea"), bool
                ):
                    raise GenerazioneInterrotta(
                        "risposta",
                        f"L'analisi dell'AI non dice se la foto {foto.id} è idonea.",
                        ANALISI,
                    )
                risultati[foto.id] = {c: analisi.get(c) for c in _CAMPI_ANALISI}
            break

    for foto in senza_analisi:
        campagne.aggiorna_foto(db, foto.id, risultati[foto.id], foto.n_utilizzi)


# --- Piano --------------------------------------------------------------------


def _campagna_ai(campagna: Any) -> CampagnaAI:
    return CampagnaAI(
        titolo=campagna.titolo,
        inizio=campagna.inizio,
        fine=campagna.fine,
        descrizione=campagna.descrizione,
        obiettivo=campagna.obiettivo,
    )


def _snapshot(campagna: Any) -> dict[str, Any]:
    fotografia = campagna.profilo_snapshot
    return fotografia if isinstance(fotografia, dict) else {}


def _gruppi_preselezionati_ai(
    gruppi: list[Any], limiti: dict[str, Any]
) -> list[GruppoAI]:
    """I gruppi per l'AI, con le sole foto preselezionate (R-05).

    Un gruppo senza foto preselezionate non va all'AI; le foto che restano
    fuori sono non usate.
    """
    ammesse = {
        foto for limite in limiti.values() for foto in limite["foto_disponibili"]
    }
    per_l_ai = []
    for gruppo in gruppi:
        scelte = [foto for foto in gruppo.foto if foto.id in ammesse]
        if scelte:
            per_l_ai.append(_gruppo_ai(gruppo, scelte))
    return per_l_ai


def _pianifica(db: Session, campagna: Any, adesso: datetime) -> None:
    """Chiede il piano, lo controlla e lo salva con uscite e post.

    All'AI vanno solo le foto migliori per punteggio, fino ai post chiesti; i
    post che quelle foto non coprono hanno un'immagine AI (R-05, R-28). Un
    piano che non passa il controllo si fa riscrivere, al massimo 3 volte:
    dopo vale come errore `risposta` (R-09).
    """
    gruppi = _caricate(db, campagna.id)
    limiti = limiti_per_canale(
        _canali(campagna),
        artigiani.post_a_settimana(campagna.frequenza),
        campagna.inizio,
        campagna.fine,
        gruppi,
    )
    margine = leggi_impostazioni().margine_slot_minuti
    gruppi_ai = _gruppi_preselezionati_ai(gruppi, limiti)

    with _nella_tappa(PIANO):
        ai = ottieni_ai()
        precedente, violazioni = None, None
        for _ in range(1 + RISCRITTURE):
            scritto = ai.pianifica_campagna(
                _snapshot(campagna),
                _campagna_ai(campagna),
                gruppi_ai,
                limiti,
                SCHEDE_CANALE,
                non_prima_di=adesso + timedelta(minutes=margine),
                piano_precedente=precedente,
                violazioni=violazioni,
            )
            service.registra_chiamata_ai(db, campagna.id, ai.ultimo_uso)
            violazioni = controlla_piano(
                scritto.contenuto,
                limiti=limiti,
                gruppi=gruppi,
                inizio=campagna.inizio,
                fine=campagna.fine,
                adesso=adesso,
                margine_minuti=margine,
            )
            if not violazioni:
                break
            precedente = scritto.contenuto
        else:
            raise GenerazioneInterrotta(
                "risposta",
                f"Il piano dell'AI non rispetta le regole dopo {RISCRITTURE} "
                f"riscritture. {violazioni[0]['messaggio']}",
                PIANO,
                violazioni[0]["canale"],
            )

    numero = db.scalar(
        select(func.max(Piano.numero)).where(Piano.campagna_id == campagna.id)
    )
    db.add(
        Piano(
            campagna_id=campagna.id,
            numero=(numero or 0) + 1,
            strategia=scritto.contenuto["strategia"],
            contenuto=scritto.contenuto,
            esito_controllo=[],
            debole=False,
            provider_ai=scritto.provider,
            modello_ai=scritto.modello,
            versione_prompt=scritto.versione_prompt,
        )
    )
    for uscita in scritto.contenuto["uscite"]:
        riga = Uscita(
            campagna_id=campagna.id,
            gruppo_id=uscita.get("gruppo_id"),
            numero=uscita["numero"],
            tema=uscita["tema"],
        )
        db.add(riga)
        db.flush()
        for post in uscita["post"]:
            db.add(
                Post(
                    campagna_id=campagna.id,
                    uscita_id=riga.id,
                    canale=post["canale"],
                    formato=post["formato"],
                    riempitivo=post.get("riempitivo"),
                    data_ora=datetime.fromisoformat(post["data_ora"]),
                    stato=DA_APPROVARE,
                )
            )
    db.flush()


# --- Testi --------------------------------------------------------------------


def _foto_del_piano(piano: Piano, numero_uscita: int, canale: str) -> list[int]:
    """Le foto che il piano ha dato al post di quell'uscita su quel canale."""
    for uscita in piano.contenuto.get("uscite", []):
        if uscita.get("numero") != numero_uscita:
            continue
        for post in uscita.get("post", []):
            if post.get("canale") == canale:
                return list(post.get("foto", []))
    return []


def _gruppo_dell_uscita(db: Session, campagna: Any, uscita: Uscita) -> Any | None:
    """Il gruppo dell'uscita; `None` se non ne ha."""
    if uscita.gruppo_id is None:
        return None
    for gruppo in _caricate(db, campagna.id):
        if gruppo.id == uscita.gruppo_id:
            return gruppo
    return None


def _scrivi(db: Session, campagna: Any, post: Post) -> None:
    """Scrive la versione 1 del post: immagine AI se serve, testo, validatore.

    Un post `immagine_ai` ha l'immagine della sua uscita, creata dal primo dei
    suoi post che si scrive; il testo porta in fondo «Immagine creata con AI»,
    aggiunta dal codice (R-43). Se l'immagine non nasce (`richiesta` o `rifiuto`
    anche alla seconda prova) il post resta senza foto, con un blocco, e la
    generazione continua (R-35).

    Un testo con blocchi o avvisi si fa riscrivere, al massimo 3 volte; poi
    si tiene l'ultimo, e il post è `da_rivedere` solo se ha un blocco (R-09).
    Un errore `richiesta` o `rifiuto` sul testo dà una versione vuota con un
    blocco, e la generazione continua (R-35).
    """
    uscita = db.get(Uscita, post.uscita_id)
    piano = service.piano_corrente(db, campagna.id)
    snapshot = _snapshot(campagna)
    ai = ottieni_ai()
    errori_immagine: list[dict[str, Any]] = []

    if post.riempitivo == IMMAGINE_AI:
        with _nella_tappa(IMMAGINI, post.canale):
            esito = immagine_del_post(db, campagna, ai, post, uscita.tema)
        foto = [esito.foto] if esito.foto is not None else []
        if esito.errore is not None:
            errori_immagine = [blocco_immagine_non_creata(esito.errore)]
    else:
        # L'ordine delle foto è quello del piano.
        ids = _foto_del_piano(piano, uscita.numero, post.canale)
        per_id = {una.id: una for una in campagne.foto_per_id(db, ids)}
        foto = [per_id[uno] for uno in ids if uno in per_id]
    gruppo = _gruppo_dell_uscita(db, campagna, uscita)
    da_scrivere = PostAI(
        canale=post.canale,
        tema=uscita.tema,
        formato=post.formato,
        data_ora=post.data_ora,
        riempitivo=post.riempitivo,
        descrizione_gruppo=gruppo.descrizione if gruppo is not None else None,
        # Un'immagine AI non è analizzata: all'AI va che cosa le è stato chiesto di mostrare.
        foto=[] if post.riempitivo == IMMAGINE_AI else [_foto_ai(una) for una in foto],
        immagine_ai=(
            descrizione_immagine(campagna, post, uscita.tema)
            if post.riempitivo == IMMAGINE_AI and foto
            else None
        ),
    )

    with _nella_tappa(TESTI, post.canale):
        try:
            scritto, errori = _testo_validato(
                db,
                ai,
                campagna,
                da_scrivere,
                snapshot,
                post.id,
                dicitura=post.riempitivo == IMMAGINE_AI and bool(foto),
            )
            testo, hashtag = scritto.testo, list(scritto.hashtag)
            firma = (scritto.provider, scritto.modello, scritto.versione_prompt)
        except ErroreAI as errore:
            if errore.tipo not in ("richiesta", "rifiuto"):
                raise
            testo, hashtag, firma = "", [], (None, None, None)
            errori = [
                {
                    "livello": BLOCCO,
                    "regola": TESTO_VUOTO,
                    "messaggio": f"Il testo non è stato scritto. {errore.messaggio}",
                }
            ]
    errori = errori_immagine + errori

    versione = VersionePost(
        post_id=post.id,
        numero=1,
        testo=testo,
        hashtag=hashtag,
        autore_id=None,
        tipo_intervento="generazione",
        provider_ai=firma[0],
        modello_ai=firma[1],
        versione_prompt=firma[2],
        errori_validazione=errori,
    )
    db.add(versione)
    db.flush()
    for posizione, una in enumerate(foto, start=1):
        db.add(
            VersionePostFoto(
                versione_id=versione.id, posizione=posizione, foto_id=una.id
            )
        )
        campagne.aggiorna_foto(db, una.id, una.analisi_ai, una.n_utilizzi + 1)
    post.da_rivedere = any(errore["livello"] == BLOCCO for errore in errori)
    db.flush()


def attacchi_degli_altri_post(
    db: Session, campagna_id: int, canale: str, post_id: int
) -> list[str]:
    """La prima frase dei testi già scritti degli altri post dello stesso canale.

    Al massimo ``ATTACCHI_MAX`` frasi di ``ATTACCO_LUNGHEZZA`` caratteri, nell'ordine
    delle uscite: l'AI non comincia il nuovo testo come loro (post v3).
    """
    altri = db.scalars(
        select(Post)
        .where(
            Post.campagna_id == campagna_id,
            Post.canale == canale,
            Post.id != post_id,
        )
        .order_by(Post.data_ora, Post.id)
    ).all()
    attacchi: list[str] = []
    for altro in altri:
        corrente = altro.versione_corrente
        testo = corrente.testo.strip() if corrente is not None else ""
        if not testo:
            continue
        frase = re.split(r"(?<=[.!?])\s|\n", testo, maxsplit=1)[0].strip()
        attacchi.append(frase[:ATTACCO_LUNGHEZZA])
        if len(attacchi) == ATTACCHI_MAX:
            break
    return attacchi


def _testo_validato(
    db: Session,
    ai: AIAdapter,
    campagna: Any,
    post: PostAI,
    snapshot: dict[str, Any],
    post_id: int,
    *,
    dicitura: bool = False,
) -> tuple[Any, list[dict[str, Any]]]:
    """Il testo dell'AI e ciò che il validatore ci trova, dopo le riscritture.

    Con ``dicitura`` il testo porta «Immagine creata con AI» in fondo, e il
    validatore la conta nei caratteri (R-43).
    """
    precedente, errori = None, None
    altri = attacchi_degli_altri_post(db, campagna.id, post.canale, post_id)
    for _ in range(1 + RISCRITTURE):
        scritto = ai.genera_post(
            snapshot,
            _campagna_ai(campagna),
            post,
            SCHEDE_CANALE[post.canale],
            testo_precedente=precedente,
            violazioni=errori,
            altri_post=altri,
        )
        service.registra_chiamata_ai(db, campagna.id, ai.ultimo_uso, post_id=post_id)
        scritto_dall_ai = scritto.testo
        if dicitura:
            scritto = replace(scritto, testo=con_dicitura(scritto.testo))
        errori = valida_testo(scritto.testo, scritto.hashtag, post.canale, snapshot)
        if not errori:
            break
        precedente = scritto_dall_ai
    return scritto, [dict(errore) for errore in errori]


# --- Errori -------------------------------------------------------------------


def registra_errore(
    db: Session, campagna_id: int, errore: Exception, esecuzione: int
) -> bool:
    """Salva l'errore che ha fermato l'esecuzione; vero se ne serve un'altra.

    - `configurazione`: `generazione_fallita` subito.
    - gli altri tipi: nuova esecuzione, fino a 3 in tutto, poi
      `generazione_fallita`.
    - un errore imprevisto vale come `temporaneo`: senza, la campagna
      resterebbe ferma in `in_generazione`.

    Si chiama in una transazione nuova, dopo che quella del passo è stata
    annullata.
    """
    campagna = campagne.campagna(db, campagna_id)
    if isinstance(errore, GenerazioneInterrotta):
        tipo, messaggio = errore.tipo, errore.messaggio
        tappa, canale = errore.tappa, errore.canale
    else:
        tipo, canale = "temporaneo", None
        messaggio = (
            f"Errore imprevisto durante la generazione ({type(errore).__name__})."
        )
        tappa = prossima_tappa(db, campagna) or AVVIO
    db.add(
        ErroreGenerazione(
            campagna_id=campagna_id,
            tipo=tipo,
            messaggio=messaggio,
            tappa=tappa,
            canale=canale,
        )
    )
    db.flush()
    if campagna.stato not in ("inviata", "in_generazione"):
        return False
    if tipo == "configurazione" or esecuzione >= ESECUZIONI:
        campagne.cambia_stato(db, campagna, "generazione_fallita")
        notifiche.crea(
            db,
            "generazione_fallita",
            campagna_id,
            ora_di_adesso(),
            contenuto={"titolo": campagna.titolo, "errore": tipo},
        )
        return False
    return True
