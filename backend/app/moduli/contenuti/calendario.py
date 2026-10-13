"""T3-12 MVP: calendario approvato, con elenco dei post per giorno."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.errori import NonTrovato
from app.core.orologio import ROMA
from app.moduli.campagne import service as campagne

from . import service
from .domain import APPROVATO, PUBBLICATO, FALLITO, ANNULLATO, SCADUTO
from .schemas import (
    CalendarioCampagna,
    GiornoCalendario,
    PostCalendario,
    FotoCalendario,
    CanaleToltoCalendario,
)


def leggi(
    db: Session, campagna_id: int, utente_id: int, ruolo: str
) -> CalendarioCampagna:
    campagna = campagne.campagna_per_calendario(db, campagna_id, utente_id, ruolo)
    piano = service.piano_corrente(db, campagna_id)
    tutti = service.post_della_campagna(db, campagna_id)
    visibili = [
        p for p in tutti if p.stato in (APPROVATO, PUBBLICATO, FALLITO, ANNULLATO)
    ]
    foto_ids = {
        legame.foto_id
        for post in visibili
        if post.versione_corrente is not None
        for legame in post.versione_corrente.legami_foto
    }
    immagini = {f.id: f for f in campagne.foto_per_id(db, foto_ids)}
    giorni: dict[date, list[PostCalendario]] = {}
    for post in visibili:
        versione = post.versione_corrente
        foto = []
        if versione is not None:
            for legame in sorted(versione.legami_foto, key=lambda l: l.posizione):
                immagine = immagini.get(legame.foto_id)
                if immagine is None:
                    continue
                if immagine.profilo_id != campagna.profilo_id:
                    raise NonTrovato("Foto non trovata.")
                foto.append(
                    FotoCalendario(
                        id=immagine.id,
                        url=f"/api/foto/{immagine.id}/file",
                        mime=immagine.mime,
                        larghezza=immagine.larghezza,
                        altezza=immagine.altezza,
                        origine=immagine.origine,
                    )
                )
        locale = post.data_ora.astimezone(ROMA)
        giorni.setdefault(locale.date(), []).append(
            PostCalendario(
                id=post.id,
                data_ora=post.data_ora,
                ora=locale.strftime("%H:%M"),
                canale=post.canale,
                stato=post.stato,
                testo=versione.testo if versione is not None else "",
                hashtag=list(versione.hashtag) if versione is not None else [],
                foto=foto,
            )
        )
    note = {d.canale: d.nota for d in campagne.decisioni_canali_tolti(db, campagna_id)}
    return CalendarioCampagna(
        campagna_id=campagna_id,
        strategia=piano.strategia if piano is not None else None,
        giorni=[
            GiornoCalendario(data=data, post=post)
            for data, post in sorted(giorni.items())
        ],
        canali_tolti=[
            CanaleToltoCalendario(canale=c, nota=note.get(c))
            for c in (campagna.canali_tolti or [])
        ],
        n_post_scaduti=sum(p.stato == SCADUTO for p in tutti),
    )
