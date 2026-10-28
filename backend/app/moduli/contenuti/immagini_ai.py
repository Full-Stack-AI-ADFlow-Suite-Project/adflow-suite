"""Immagini AI dei post di rimpiazzo (spec R-28, R-43, R-44; brief-ai T3-34).

Un'uscita senza foto ha un'immagine sola, la stessa su tutti i canali: la crea
il primo dei suoi post che si scrive, gli altri la trovano già fatta. Così una
nuova esecuzione non la ricrea (R-24).
"""

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.ai import AIAdapter, ErroreAI, prompt_immagine
from app.adapters.ai.schemi import INQUADRATURE
from app.adapters.archivio import ottieni_archivio
from app.core.orologio import ROMA
from app.moduli.campagne import service as campagne

from . import service
from .domain import DICITURA_IMMAGINE_AI, IMMAGINE_AI
from .models import Post, Uscita

ORIGINE = "creata_ai"
ESTENSIONI = {"image/png": "png", "image/jpeg": "jpg"}
# La regola di un blocco senza testo, nella versione del post che non ha l'immagine.
IMMAGINE_NON_CREATA = "immagine_non_creata"


@dataclass
class EsitoImmagine:
    """L'immagine del post, o il motivo per cui non c'è (``errore``)."""

    foto: Any | None = None
    errore: str | None = None
    # Chi ha creato l'immagine: finiscono nella versione del post.
    provider: str | None = None
    modello: str | None = None
    versione_prompt: str | None = None


def con_dicitura(testo: str) -> str:
    """Il testo con «Immagine creata con AI» in fondo, una volta sola (R-43)."""
    if testo.rstrip().endswith(DICITURA_IMMAGINE_AI):
        return testo
    return f"{testo.rstrip()}\n\n{DICITURA_IMMAGINE_AI}"


def senza_dicitura(testo: str) -> str:
    """Il testo senza «Immagine creata con AI» in fondo (R-36).

    Serve quando un post passa da un'immagine AI a una foto vera: la dicitura
    non ha più senso. Il resto del testo non cambia.
    """
    ripulito = testo.rstrip()
    if ripulito.endswith(DICITURA_IMMAGINE_AI):
        return ripulito[: -len(DICITURA_IMMAGINE_AI)].rstrip()
    return testo


def stile_delle_foto(db: Session, campagna_id: int) -> str | None:
    """Ciò che le descrizioni delle foto vere dicono di luce, sfondi e colori (T3-920).

    Al massimo 400 caratteri; ``None`` se la campagna non ha foto vere
    analizzate. Le immagini AI restano fuori: lo stile è quello delle foto
    dell'artigiano.
    """
    descrizioni = []
    for foto in campagne.foto_della_campagna(db, campagna_id):
        if foto.origine != "caricata":
            continue
        analisi = foto.analisi_ai or {}
        descrizione = analisi.get("descrizione")
        if isinstance(descrizione, str) and descrizione.strip():
            descrizioni.append(" ".join(descrizione.split()))
    if not descrizioni:
        return None
    return " · ".join(dict.fromkeys(descrizioni))[:400].rstrip()


def scena_dell_uscita(db: Session, uscita: Any) -> dict[str, Any] | None:
    """La scena dell'uscita dal piano corrente, se c'è e è ben formata (T3-910).

    La scena sta dentro ``piano.contenuto``, accanto ai post dell'uscita:
    nessuna colonna nuova. Una scena mancante, malformata o con
    un'inquadratura sconosciuta vale ``None``: non è una violazione del piano
    e l'immagine parte dal tema, come oggi.
    """
    piano = service.piano_corrente(db, uscita.campagna_id)
    if piano is None or not isinstance(piano.contenuto, dict):
        return None
    for voce in piano.contenuto.get("uscite") or []:
        if not isinstance(voce, dict) or voce.get("numero") != uscita.numero:
            continue
        scena = voce.get("scena")
        if not isinstance(scena, dict):
            return None
        campi = ("soggetto", "inquadratura", "luce", "colori")
        if not all(
            isinstance(scena.get(campo), str) and scena[campo].strip()
            for campo in campi
        ):
            return None
        if scena["inquadratura"] not in INQUADRATURE:
            return None
        return scena
    return None


def blocco_immagine_non_creata(errore: str) -> dict[str, str]:
    """La voce di ``errori_validazione`` di un post la cui immagine non è nata."""
    return {
        "livello": "blocco",
        "regola": IMMAGINE_NON_CREATA,
        "messaggio": f"Immagine non creata. {errore}",
    }


def _gia_deciso(db: Session, post: Post) -> EsitoImmagine | None:
    """Ciò che un altro post della stessa uscita ha già trovato: immagine o blocco."""
    altri = db.scalars(
        select(Post)
        .where(
            Post.uscita_id == post.uscita_id,
            Post.id != post.id,
            Post.riempitivo == IMMAGINE_AI,
        )
        .order_by(Post.id)
    )
    for altro in altri:
        versione = altro.versione_corrente
        if versione is None:
            continue
        foto = campagne.foto_per_id(db, [l.foto_id for l in versione.legami_foto])
        creata = next((una for una in foto if una.origine == ORIGINE), None)
        if creata is not None:
            return EsitoImmagine(foto=creata)
        for errore in versione.errori_validazione or []:
            if errore["regola"] == IMMAGINE_NON_CREATA:
                return EsitoImmagine(errore=errore["messaggio"])
    return None


def descrizione_immagine(db: Session, campagna: Any, post: Post, tema: str) -> str:
    """Che cosa mostra l'immagine AI del post: il prompt con cui è stata chiesta.

    Va a chi scrive il testo, che non vede l'immagine ma deve richiamarla. È lo
    stesso prompt della generazione, con la scena, la campagna e lo stile delle
    foto vere (T3-920).
    """
    snapshot = campagna.profilo_snapshot
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    return prompt_immagine(
        snapshot,
        tema,
        post.data_ora.astimezone(ROMA).date(),
        campagna=_campagna_immagine(campagna),
        scena=_scena_del_post(db, post),
        stile=stile_delle_foto(db, campagna.id),
    )


def _campagna_immagine(campagna: Any) -> dict[str, str]:
    """Titolo, descrizione e obiettivo della campagna per il prompt (T3-920)."""
    return {
        "titolo": campagna.titolo or "",
        "descrizione": campagna.descrizione or "",
        "obiettivo": campagna.obiettivo or "",
    }


def _scena_del_post(db: Session, post: Post) -> dict[str, Any] | None:
    """La scena dell'uscita del post, se il piano corrente la contiene."""
    uscita = db.get(Uscita, post.uscita_id)
    return scena_dell_uscita(db, uscita) if uscita is not None else None


def immagine_del_post(
    db: Session, campagna: Any, ai: AIAdapter, post: Post, tema: str
) -> EsitoImmagine:
    """L'immagine AI di un post `immagine_ai`: quella dell'uscita, o una nuova.

    Se il provider non accetta il prompt (`richiesta` o `rifiuto`) si prova una
    seconda volta con un prompt senza tono né stagione; se fallisce ancora il
    post resta senza foto e la generazione continua (R-35). Ogni altro errore
    dell'AI esce. La chiamata riuscita si registra subito in `chiamata_ai`
    (R-44). Senza commit.
    """
    esistente = _gia_deciso(db, post)
    if esistente is not None:
        return esistente
    snapshot = campagna.profilo_snapshot
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    giorno = post.data_ora.astimezone(ROMA).date()
    scena = _scena_del_post(db, post)
    stile = stile_delle_foto(db, campagna.id)
    dati_campagna = _campagna_immagine(campagna)

    ultimo: ErroreAI | None = None
    for semplice in (False, True):
        prompt = prompt_immagine(
            snapshot,
            tema,
            giorno,
            semplice=semplice,
            campagna=dati_campagna,
            scena=scena,
            stile=stile,
        )
        try:
            immagine = ai.genera_immagine(prompt)
        except ErroreAI as errore:
            if errore.tipo not in ("richiesta", "rifiuto"):
                raise
            ultimo = errore
            continue
        service.registra_chiamata_ai(db, campagna.id, ai.ultimo_uso, post_id=post.id)
        return EsitoImmagine(foto=_salva(db, campagna.id, immagine, prompt=prompt))
    return EsitoImmagine(errore=ultimo.messaggio if ultimo else "")


def immagine_rigenerata(
    db: Session,
    campagna: Any,
    ai: AIAdapter,
    post: Post,
    tema: str,
    nota: str | None,
    da_evitare: list[str],
) -> EsitoImmagine:
    """Una nuova immagine AI per l'uscita del post (R-49).

    Come ``immagine_del_post``: un rifiuto del provider si riprova una volta
    con il prompt semplice; due rifiuti lasciano il post senza immagine nuova
    e chi chiama spegne l'intervento. Il prompt con cui è nata resta in
    ``foto.analisi_ai``; la chiamata riuscita si registra subito in
    ``chiamata_ai`` (R-44).
    """
    snapshot = campagna.profilo_snapshot
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    giorno = post.data_ora.astimezone(ROMA).date()
    scena = _scena_del_post(db, post)
    stile = stile_delle_foto(db, campagna.id)
    dati_campagna = _campagna_immagine(campagna)

    ultimo: ErroreAI | None = None
    for semplice in (False, True):
        prompt = prompt_immagine(
            snapshot,
            tema,
            giorno,
            semplice=semplice,
            nota=nota,
            da_evitare=da_evitare,
            campagna=dati_campagna,
            scena=scena,
            stile=stile,
        )
        try:
            immagine = ai.genera_immagine(prompt)
        except ErroreAI as errore:
            if errore.tipo not in ("richiesta", "rifiuto"):
                raise
            ultimo = errore
            continue
        service.registra_chiamata_ai(db, campagna.id, ai.ultimo_uso, post_id=post.id)
        return EsitoImmagine(
            foto=_salva(db, campagna.id, immagine, prompt=prompt, nota=nota),
            provider=immagine.provider,
            modello=immagine.modello,
            versione_prompt=immagine.versione_prompt,
        )
    return EsitoImmagine(errore=ultimo.messaggio if ultimo else "")


def _salva(
    db: Session,
    campagna_id: int,
    immagine: Any,
    *,
    prompt: str | None = None,
    nota: str | None = None,
) -> Any:
    """Il file nell'archivio e la foto `creata_ai`, senza gruppo.

    Se la foto non si crea, il file appena salvato si elimina. Se la transazione
    di chi chiama viene annullata più tardi, il file resta senza foto: è un file
    orfano, innocuo. Con ``prompt`` la foto porta in ``analisi_ai`` il prompt con
    cui è nata (R-49).
    """
    with Image.open(BytesIO(immagine.contenuto)) as aperta:
        larghezza, altezza = aperta.size
    archivio = ottieni_archivio()
    file = archivio.salva(immagine.contenuto, ESTENSIONI[immagine.mime])
    try:
        foto = campagne.aggiungi_foto(
            db, campagna_id, ORIGINE, file, immagine.mime, larghezza, altezza
        )
        if prompt is not None:
            campagne.aggiorna_foto(
                db,
                foto.id,
                {
                    "prompt": prompt,
                    "versione_prompt": immagine.versione_prompt,
                    "nota": nota,
                },
                foto.n_utilizzi or 0,
            )
        return foto
    except Exception:
        archivio.elimina(file)
        raise
