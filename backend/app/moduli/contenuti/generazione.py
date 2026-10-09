"""Generazione di una campagna, a tappe (plan §4, spec §2.2).

Il job chiama ``passo()`` finché c'è lavoro, ogni volta in una transazione
sua. Un passo guarda ciò che è già salvato e fa la prima cosa che manca:

1. avvio: la campagna `inviata` diventa `in_generazione`;
2. analisi: un gruppo di foto caricate non ancora analizzato;
3. piano: piano dell'AI, controllo, righe `piano`, `uscita`, `post`;
4. testi: un post senza versione, con la sua cartolina se è un riempitivo;
5. fine: la campagna passa `in_revisione`.

Per questo una nuova esecuzione, Riprova e Prosegui riprendono da sole dal
punto giusto (R-24). Se un passo solleva un errore, la sua transazione si
annulla e ``registra_errore()`` decide che cosa succede alla campagna (R-35).
Si usa sempre la fotografia del profilo, mai il profilo corrente (R-11).
"""

from collections.abc import Iterator
from contextlib import contextmanager
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
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne

from . import service
from .cartoline import componi_cartolina
from .domain import DA_APPROVARE, SCHEDE_CANALE
from .models import (
    ErroreGenerazione,
    Piano,
    Post,
    Uscita,
    VersionePost,
    VersionePostFoto,
)
from .piano import controlla_piano, limiti_per_canale, piano_debole
from .validatore import BLOCCO, TESTO_VUOTO, valida_testo

# plan §4: il job gira al massimo 3 volte, a 30 secondi una dall'altra.
ESECUZIONI = 3
ATTESA_SECONDI = 30
# R-09: piano e testo si riscrivono al massimo 3 volte.
RISCRITTURE = 3
# Un passo è un gruppo, il piano o un post: molti più passi sono un errore.
MAX_PASSI = 1000

AVVIO = "avvio"
ANALISI = "analisi"
PIANO = "piano"
TESTI = "testi"
FINE = "fine"
TAPPE = (AVVIO, ANALISI, PIANO, TESTI, FINE)

_CAMPI_ANALISI = ("idonea", "simile_a", "tipo", "punteggio", "motivo", "soggetto")


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


def _gruppo_da_analizzare(db: Session, campagna_id: int) -> Any | None:
    for gruppo in _caricate(db, campagna_id):
        if any(foto.analisi_ai is None for foto in gruppo.foto):
            return gruppo
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
    if _gruppo_da_analizzare(db, campagna.id) is not None:
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
        _analizza(db, _gruppo_da_analizzare(db, campagna_id))
        return True
    if tappa == PIANO:
        return _pianifica(db, campagna, adesso)
    if tappa == TESTI:
        _scrivi(db, campagna, _post_da_scrivere(db, campagna))
        return True
    campagne.cambia_stato(db, campagna, "in_revisione")
    return False


# --- Analisi ------------------------------------------------------------------


def _foto_ai(foto: Any) -> FotoAI:
    analisi = foto.analisi_ai if isinstance(foto.analisi_ai, dict) else None
    return FotoAI(
        id=foto.id,
        file=foto.file,
        mime=foto.mime,
        da_usare=bool(foto.da_usare),
        analisi=analisi,
    )


def _gruppo_ai(gruppo: Any, foto: list[Any]) -> GruppoAI:
    return GruppoAI(
        id=gruppo.id,
        descrizione=gruppo.descrizione,
        da_usare_il=gruppo.da_usare_il,
        foto=[_foto_ai(una) for una in foto],
    )


def _non_idonea(motivo: str) -> dict[str, Any]:
    return dict.fromkeys(_CAMPI_ANALISI) | {"idonea": False, "motivo": motivo}


def _analizza(db: Session, gruppo: Any) -> None:
    """Analizza le foto del gruppo che non hanno ancora un'analisi (R-24).

    Un errore `richiesta` o `rifiuto` su una sola foto la rende non idonea,
    con il motivo, e l'analisi continua con le altre (R-35).
    """
    da_fare = [foto for foto in gruppo.foto if foto.analisi_ai is None]
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

    _stelle_mai_doppioni(gruppo, risultati)
    for foto in gruppo.foto:
        if foto.id in risultati:
            campagne.aggiorna_foto(db, foto.id, risultati[foto.id], foto.n_utilizzi)


def _stelle_mai_doppioni(gruppo: Any, risultati: dict[int, dict[str, Any]]) -> None:
    """Una foto con la stella non resta `simile_a`: il doppione è l'altra (R-23)."""
    stelle = {foto.id for foto in gruppo.foto if foto.da_usare}
    for foto_id in sorted(stelle & set(risultati)):
        altra = risultati[foto_id].get("simile_a")
        if altra is None:
            continue
        risultati[foto_id]["simile_a"] = None
        dell_altra = risultati.get(altra)
        if (
            altra not in stelle
            and dell_altra is not None
            and not dell_altra.get("simile_a")
        ):
            dell_altra["simile_a"] = foto_id


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


def _pianifica(db: Session, campagna: Any, adesso: datetime) -> bool:
    """Chiede il piano, lo controlla e lo salva con uscite e post.

    Un piano che non passa il controllo si fa riscrivere, al massimo 3 volte:
    dopo vale come errore `risposta` (R-09). Il piano debole si salva lo
    stesso, con i suoi post, e ferma la campagna in `piano_da_rivedere`
    (R-20): restituisce falso.
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
    gruppi_ai = [_gruppo_ai(gruppo, gruppo.foto) for gruppo in gruppi]

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

    debole = piano_debole(limiti, gruppi)
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
            debole=debole,
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

    if debole:
        campagne.cambia_stato(db, campagna, "piano_da_rivedere")
        return False
    return True


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


def _scrivi(db: Session, campagna: Any, post: Post) -> None:
    """Scrive la versione 1 del post: cartolina se serve, testo, validatore.

    Un testo con blocchi o avvisi si fa riscrivere, al massimo 3 volte; poi
    si tiene l'ultimo, e il post è `da_rivedere` solo se ha un blocco (R-09).
    Un errore `richiesta` o `rifiuto` dà una versione vuota con un blocco, e
    la generazione continua (R-35).
    """
    uscita = db.get(Uscita, post.uscita_id)
    piano = service.piano_corrente(db, campagna.id)
    foto_della_campagna = {
        foto.id: foto for foto in campagne.foto_della_campagna(db, campagna.id)
    }
    snapshot = _snapshot(campagna)

    if post.riempitivo == "cartolina":
        foto = [componi_cartolina(db, campagna, uscita.tema)]
    else:
        ids = _foto_del_piano(piano, uscita.numero, post.canale)
        foto = [foto_della_campagna[uno] for uno in ids if uno in foto_della_campagna]
    gruppo = next(
        (g for g in _caricate(db, campagna.id) if g.id == uscita.gruppo_id), None
    )
    da_scrivere = PostAI(
        canale=post.canale,
        tema=uscita.tema,
        formato=post.formato,
        data_ora=post.data_ora,
        riempitivo=post.riempitivo,
        descrizione_gruppo=gruppo.descrizione if gruppo is not None else None,
        foto=[_foto_ai(una) for una in foto],
    )

    with _nella_tappa(TESTI, post.canale):
        ai = ottieni_ai()
        try:
            scritto, errori = _testo_validato(ai, campagna, da_scrivere, snapshot)
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


def _testo_validato(
    ai: AIAdapter, campagna: Any, post: PostAI, snapshot: dict[str, Any]
) -> tuple[Any, list[dict[str, Any]]]:
    """Il testo dell'AI e ciò che il validatore ci trova, dopo le riscritture."""
    precedente, errori = None, None
    for _ in range(1 + RISCRITTURE):
        scritto = ai.genera_post(
            snapshot,
            _campagna_ai(campagna),
            post,
            SCHEDE_CANALE[post.canale],
            testo_precedente=precedente,
            violazioni=errori,
        )
        errori = valida_testo(scritto.testo, scritto.hashtag, post.canale, snapshot)
        if not errori:
            break
        precedente = scritto.testo
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
        return False
    return True
