"""Interventi dell'operatore sul testo di un post (spec §3, R-30)."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.adapters.ai import PostAI, ottieni_ai
from app.core.errori import DatiNonValidi, StatoNonValido
from app.moduli.campagne import service as campagne

from .domain import DA_APPROVARE, SCHEDE_CANALE, TIPI_INTERVENTO_IN_CORSO
from .generazione import (
    RISCRITTURE,
    _campagna_ai,
    _foto_ai,
    _gruppo_dell_uscita,
    _snapshot,
)
from .models import Post, Uscita, VersionePost, VersionePostFoto
from .service import (
    _azzera_spunta,
    _intervento_attivo,
    _post,
    registra_chiamata_ai,
)
from .validatore import BLOCCO, valida_testo

# R-03: al massimo 3 rigenerazioni del testo per post (da zero e da proposta insieme).
MAX_RIGENERAZIONI = 3
RIGENERAZIONI = ("rigenera_totale", "rigenera_da_proposta")


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
    """La modifica a mano come nuova versione ``modifica_operatore`` (R-30, CA-64).

    La versione ha lo stesso gruppo di foto della corrente e passa dal
    validatore (R-09): con un blocco, o con testo e hashtag uguali a quelli
    correnti, non si salva niente. Non conta cicli (R-03), azzera la spunta e,
    non avendo blocchi, toglie a un post ``da_rivedere`` il suo indicatore.
    Gli avvisi si salvano con la versione e non fermano nulla.
    """
    record = _post(db, post_id)
    campagna = campagne.campagna(db, record.campagna_id)
    if campagna.stato != "in_revisione":
        raise StatoNonValido("La campagna non è in revisione.")
    if record.stato != DA_APPROVARE:
        raise StatoNonValido("Il post non è da approvare.")
    if _intervento_attivo(record, adesso):
        raise StatoNonValido("Sul post c'è un intervento in corso.")
    corrente = record.versione_corrente
    if corrente is None:
        raise StatoNonValido("Il post non ha ancora un testo da modificare.")

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


def _si_puo_intervenire(post: Post, campagna, adesso: datetime) -> bool:
    """Campagna in revisione, post da approvare, nessun intervento in corso (R-16, R-31)."""
    return (
        campagna.stato == "in_revisione"
        and post.stato == DA_APPROVARE
        and not _intervento_attivo(post, adesso)
    )


def puo_rigenerare(db: Session, post_id: int, adesso: datetime) -> bool:
    """Vero se si può chiedere una rigenerazione del testo (R-03, R-31)."""
    record = _post(db, post_id)
    campagna = campagne.campagna(db, record.campagna_id)
    return (
        _si_puo_intervenire(record, campagna, adesso)
        and record.n_rigenerazioni_testo < MAX_RIGENERAZIONI
    )


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
    elif not _si_puo_intervenire(record, campagna, adesso):
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
    gruppo = _gruppo_dell_uscita(db, campagna, uscita, record.canale, adesso)
    da_scrivere = PostAI(
        canale=record.canale,
        tema=uscita.tema,
        formato=record.formato,
        data_ora=record.data_ora,
        riempitivo=record.riempitivo,
        descrizione_gruppo=gruppo.descrizione if gruppo is not None else None,
        foto=[_foto_ai(una) for una in foto],
    )
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
        registra_chiamata_ai(db, campagna.id, ai.ultimo_uso, post_id=record.id)
        errori = valida_testo(scritto.testo, scritto.hashtag, record.canale, snapshot)
        if not errori:
            break
        precedente = scritto.testo
    errori = [dict(errore) for errore in errori]

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
