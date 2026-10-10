"""Logica e operazioni per l'archivio della bottega (T2a-22, spec R-13, R-27)."""

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.adapters.archivio import ottieni_archivio
from app.core.errori import DatiNonValidi, NonTrovato, StatoNonValido
from app.moduli.artigiani import service as artigiani_service
from .immagini import (
    MAX_FOTO_PER_GRUPPO,
    analizza_e_valida_immagine,
)
from .models import Foto, GruppoFoto
from .schemas import (
    FotoDettaglio,
    GruppoArchivioCrea,
    GruppoSintetico,
)
from .service import _al_termine_transazione


def elenca_archivio(db: Session, utente_id: int) -> list[GruppoSintetico]:
    """Elenca i gruppi e le foto senza campagna dell'archivio della bottega (GET /archivio)."""
    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None:
        raise NonTrovato("Profilo bottega non trovato.")

    gruppi = list(
        db.scalars(
            select(GruppoFoto)
            .where(
                GruppoFoto.profilo_id == profilo.id,
                GruppoFoto.campagna_id.is_(None),
            )
            .order_by(GruppoFoto.id)
        )
    )
    return [GruppoSintetico.model_validate(g) for g in gruppi]


def crea_gruppo_archivio(
    db: Session, utente_id: int, dati: GruppoArchivioCrea
) -> GruppoSintetico:
    """Crea un gruppo di foto caricate senza campagna per l'archivio (POST /archivio/gruppi)."""
    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None:
        raise NonTrovato("Profilo bottega non trovato.")

    db.execute(text("SELECT pg_advisory_xact_lock(:chiave)"), {"chiave": profilo.id})

    gruppo = GruppoFoto(
        profilo_id=profilo.id,
        campagna_id=None,
        origine="caricate",
        descrizione=dati.descrizione,
        da_usare_il=None,
        n_immagini=None,
    )
    db.add(gruppo)
    db.flush()
    return GruppoSintetico.model_validate(gruppo)


def carica_foto_archivio(
    db: Session, utente_id: int, gruppo_id: int, contenuto: bytes
) -> FotoDettaglio:
    """Carica una foto nell'archivio della bottega associandola al gruppo (POST /archivio/foto)."""
    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None:
        raise NonTrovato("Profilo bottega non trovato.")

    db.execute(text("SELECT pg_advisory_xact_lock(:chiave)"), {"chiave": profilo.id})

    gruppo = db.scalar(
        select(GruppoFoto).where(GruppoFoto.id == gruppo_id).with_for_update()
    )
    if (
        gruppo is None
        or gruppo.profilo_id != profilo.id
        or gruppo.campagna_id is not None
    ):
        raise NonTrovato("Gruppo non trovato nell'archivio.")

    count = (
        db.scalar(select(func.count(Foto.id)).where(Foto.gruppo_id == gruppo.id)) or 0
    )
    if count >= MAX_FOTO_PER_GRUPPO:
        raise DatiNonValidi("Il gruppo non può contenere più di 20 foto.")

    info = analizza_e_valida_immagine(contenuto)

    archivio = ottieni_archivio()
    nome_file = archivio.salva(contenuto, info.estensione)
    _al_termine_transazione(db, su_rollback=lambda: archivio.elimina(nome_file))

    try:
        nuova_foto = Foto(
            profilo_id=profilo.id,
            campagna_id=None,
            gruppo_id=gruppo.id,
            origine="caricata",
            file=nome_file,
            mime=info.mime,
            larghezza=info.larghezza,
            altezza=info.altezza,
            da_usare=False,
            pubblicata_su={},
        )
        db.add(nuova_foto)
        db.flush()
        return FotoDettaglio.model_validate(nuova_foto)
    except Exception:
        archivio.elimina(nome_file)
        raise


def elimina_foto_archivio(db: Session, utente_id: int, foto_id: int) -> None:
    """Elimina una foto dall'archivio della bottega (DELETE /archivio/foto/{id})."""
    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None:
        raise NonTrovato("Profilo bottega non trovato.")

    db.execute(text("SELECT pg_advisory_xact_lock(:chiave)"), {"chiave": profilo.id})

    foto = db.scalar(select(Foto).where(Foto.id == foto_id).with_for_update())
    if foto is None or foto.profilo_id != profilo.id or foto.campagna_id is not None:
        raise NonTrovato("Foto non trovata.")

    if foto.n_utilizzi > 0:
        raise StatoNonValido(
            "La foto non può essere eliminata perché è già stata utilizzata in un post."
        )

    nome_file = foto.file
    db.delete(foto)
    db.flush()

    archivio = ottieni_archivio()

    def rimuovi_singolo() -> None:
        try:
            archivio.elimina(nome_file)
        except OSError:
            pass

    _al_termine_transazione(db, su_commit=rimuovi_singolo)


def elimina_gruppo_archivio(db: Session, utente_id: int, gruppo_id: int) -> None:
    """Elimina un gruppo dell'archivio con le sue foto (DELETE /archivio/gruppi/{id})."""
    profilo = artigiani_service.profilo_di(db, utente_id)
    if profilo is None:
        raise NonTrovato("Profilo bottega non trovato.")

    db.execute(text("SELECT pg_advisory_xact_lock(:chiave)"), {"chiave": profilo.id})

    gruppo = db.scalar(
        select(GruppoFoto).where(GruppoFoto.id == gruppo_id).with_for_update()
    )
    if (
        gruppo is None
        or gruppo.profilo_id != profilo.id
        or gruppo.campagna_id is not None
    ):
        raise NonTrovato("Gruppo non trovato.")

    if any(f.n_utilizzi > 0 for f in gruppo.foto):
        raise StatoNonValido(
            "Il gruppo non può essere eliminato perché contiene foto già utilizzate in un post."
        )

    file_da_eliminare = [f.file for f in gruppo.foto]
    for f in gruppo.foto:
        db.delete(f)
    db.delete(gruppo)
    db.flush()

    archivio = ottieni_archivio()

    def rimuovi_tutti() -> None:
        for fn in file_da_eliminare:
            try:
                archivio.elimina(fn)
            except OSError:
                pass

    _al_termine_transazione(db, su_commit=rimuovi_tutti)
