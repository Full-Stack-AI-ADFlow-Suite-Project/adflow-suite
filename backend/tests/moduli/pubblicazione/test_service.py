"""Test del service di pubblicazione (T1-43): CA-36…39, CA-52, CA-57, CA-76."""

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.adapters.social import SocialFinto, usa_social
from app.moduli.campagne import service as campagne
from app.moduli.campagne.models import Foto
from app.moduli.contenuti.models import VersionePostFoto
from app.moduli.pubblicazione.models import Pubblicazione
from app.moduli.pubblicazione.service import pubblica_dovuti
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_conclusa,
    foto,
    gruppo_di_archivio,
)
from tests.moduli.contenuti.fabbrica import post_approvato, post_da_approvare

ADESSO = datetime(2020, 1, 1, 13, tzinfo=timezone.utc)
PASSATO = datetime(2020, 1, 1, 12, tzinfo=timezone.utc)
FUTURO = datetime(2020, 1, 2, 12, tzinfo=timezone.utc)


@pytest.fixture
def social() -> Iterator[SocialFinto]:
    finto = SocialFinto()
    with usa_social(finto):
        yield finto


@pytest.fixture
def archivio() -> Iterator[ArchivioFinto]:
    finto = ArchivioFinto()
    with usa_archivio(finto):
        yield finto


def _archivia_foto(db, archivio: ArchivioFinto, campagna_id: int) -> None:
    """Rende leggibili dall'archivio i file delle foto della campagna."""
    for immagine in campagne.foto_della_campagna(db, campagna_id):
        archivio._archivio[immagine.file] = b"foto-di-prova"
    db.flush()


def _pubblicazioni(db, post_id: int) -> list[Pubblicazione]:
    return list(
        db.scalars(select(Pubblicazione).where(Pubblicazione.post_id == post_id))
    )


def test_ca36_post_approvato_dovuto_viene_pubblicato(db, social, archivio):
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    [tentativo] = _pubblicazioni(db, post.id)
    assert tentativo.stato == "ok"
    assert tentativo.id_esterno is not None
    assert tentativo.n_tentativo == 1
    db.refresh(post)
    assert post.stato == "pubblicato"


def test_ca36_due_tick_pubblicano_una_volta_sola(db, social, archivio):
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)
    pubblica_dovuti(db, ADESSO)

    ok = [p for p in _pubblicazioni(db, post.id) if p.stato == "ok"]
    assert len(ok) == 1
    assert len(social.pubblicazioni) == 1


def test_ca37_post_da_approvare_non_viene_pubblicato(db, social, archivio):
    campagna = campagna_attiva(db)
    post = post_da_approvare(db, campagna_id=campagna.id, data_ora=PASSATO)
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    assert _pubblicazioni(db, post.id) == []
    assert social.pubblicazioni == []


def test_ca37_post_approvato_non_ancora_dovuto(db, social, archivio):
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=FUTURO)
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    assert _pubblicazioni(db, post.id) == []
    assert social.pubblicazioni == []


def test_ca37_post_di_campagna_non_attiva_non_pubblicato(db, social, archivio):
    """Un post approvato di una campagna non attiva non parte (R-01)."""
    from tests.moduli.campagne.fabbrica import campagna_in_revisione

    campagna = campagna_in_revisione(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    assert _pubblicazioni(db, post.id) == []


def test_ca38_errore_temporaneo_al_terzo_tentativo_fallito(db, social, archivio):
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    post.versione_corrente.testo = "Testo con FAIL_TEMP"
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)
    [tentativo] = _pubblicazioni(db, post.id)
    assert tentativo.stato == "in_corso"
    assert tentativo.n_tentativo == 1

    pubblica_dovuti(db, ADESSO)
    assert tentativo.stato == "in_corso"
    assert tentativo.n_tentativo == 2

    pubblica_dovuti(db, ADESSO)
    assert tentativo.stato == "errore"
    assert tentativo.n_tentativo == 3
    db.refresh(post)
    assert post.stato == "fallito"
    # Tre tentativi reali verso il social, una sola riga di pubblicazione.
    assert len(social.pubblicazioni) == 3


def test_ca38_errore_definitivo_fallisce_subito(db, social, archivio):
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    post.versione_corrente.testo = "Testo con FAIL_DEF"
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    [tentativo] = _pubblicazioni(db, post.id)
    assert tentativo.stato == "errore"
    assert tentativo.errore is not None
    db.refresh(post)
    assert post.stato == "fallito"
    assert len(social.pubblicazioni) == 1


def test_ca39_tutti_i_post_chiusi_campagna_conclusa(db, social, archivio):
    campagna = campagna_attiva(db)
    post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    db.refresh(campagna)
    assert campagna.stato == "conclusa"
    assert campagna.chiusa_il is not None


def test_ca39_post_non_dovuto_tiene_aperta_la_campagna(db, social, archivio):
    campagna = campagna_attiva(db)
    post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    post_approvato(db, campagna_id=campagna.id, data_ora=FUTURO)
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    db.refresh(campagna)
    assert campagna.stato == "attiva"


def test_ca39_fallito_conclude_solo_a_periodo_finito(db, social, archivio):
    """Con un post fallito la campagna resta attiva fino alla fine (R-34)."""
    campagna = campagna_attiva(db, inizio=PASSATO.date(), fine=ADESSO.date())
    riuscito = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    rotto = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    rotto.versione_corrente.testo = "Testo con FAIL_DEF"
    _archivia_foto(db, archivio, campagna.id)

    # Oggi è ancora dentro il periodo: pubblicato + fallito, ma resta attiva.
    pubblica_dovuti(db, ADESSO)
    db.refresh(campagna)
    db.refresh(riuscito)
    db.refresh(rotto)
    assert riuscito.stato == "pubblicato"
    assert rotto.stato == "fallito"
    assert campagna.stato == "attiva"

    # Dopo la fine del periodo, a un tick qualunque, si chiude.
    dopo = datetime(2020, 1, 3, tzinfo=timezone.utc)
    pubblica_dovuti(db, dopo)
    db.refresh(campagna)
    assert campagna.stato == "conclusa"


def test_ca52_carosello_pubblicato_con_tutte_le_foto_in_ordine(db, social, archivio):
    """Un carosello parte una volta sola con le foto in ordine di posizione."""
    campagna = campagna_attiva(db)
    post = post_approvato(
        db, campagna_id=campagna.id, data_ora=PASSATO, formato="carosello"
    )
    # Aggiunge una seconda foto alla versione corrente.
    extra = foto(db, campagna=campagna)
    versione = post.versione_corrente
    db.add(VersionePostFoto(versione_id=versione.id, posizione=2, foto_id=extra.id))
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)
    pubblica_dovuti(db, ADESSO)

    assert len(social.pubblicazioni) == 1
    assert social.pubblicazioni[0]["n_foto"] == 2
    db.refresh(post)
    assert post.stato == "pubblicato"


def test_ca57_cartolina_pubblicata_con_la_sua_immagine(db, social, archivio):
    """Un post cartolina pubblica la sua immagine dedicata (CA-57)."""
    campagna = campagna_attiva(db)
    post = post_approvato(
        db, campagna_id=campagna.id, data_ora=PASSATO, riempitivo="cartolina"
    )
    cartolina = foto(db, campagna=campagna, origine="cartolina")
    [legame] = post.versione_corrente.legami_foto
    legame.foto_id = cartolina.id
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    assert len(social.pubblicazioni) == 1
    assert social.pubblicazioni[0]["n_foto"] == 1
    db.refresh(post)
    assert post.stato == "pubblicato"


def test_post_senza_foto_fallisce(db, social, archivio):
    """Un post approvato senza foto nella versione non può partire."""
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    for legame in list(post.versione_corrente.legami_foto):
        db.delete(legame)
    db.flush()
    db.expire(post.versione_corrente, ["legami_foto"])
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    [tentativo] = _pubblicazioni(db, post.id)
    assert tentativo.stato == "errore"
    db.refresh(post)
    assert post.stato == "fallito"
    assert social.pubblicazioni == []


def test_canale_non_collegato_fallisce_senza_chiamare_il_social(db, social, archivio):
    """Account non collegato: errore registrato, nessuna chiamata (R-07)."""
    campagna = campagna_attiva(db)
    post = post_approvato(
        db, campagna_id=campagna.id, data_ora=PASSATO, canale="facebook"
    )
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    [tentativo] = _pubblicazioni(db, post.id)
    assert tentativo.stato == "errore"
    assert "facebook" in tentativo.errore
    db.refresh(post)
    assert post.stato == "fallito"
    assert social.pubblicazioni == []


def test_file_mancante_nell_archivio_fallisce(db, social, archivio):
    """File non presente nell'archivio: tentativo in errore, post fallito."""
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    # Nessun file caricato nell'archivio finto.

    pubblica_dovuti(db, ADESSO)

    [tentativo] = _pubblicazioni(db, post.id)
    assert tentativo.stato == "errore"
    db.refresh(post)
    assert post.stato == "fallito"
    assert social.pubblicazioni == []


def test_ca76_foto_caricata_segnata_con_canale_e_data(db, social, archivio):
    """Dopo l'ok la foto caricata porta canale e istante in UTC (CA-76, R-27)."""
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    [legame] = post.versione_corrente.legami_foto
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    immagine = db.get(Foto, legame.foto_id)
    assert immagine.pubblicata_su == {"instagram": ADESSO.isoformat()}


def test_ca76_foto_d_archivio_di_campagna_chiusa_si_segna(db, social, archivio):
    """La foto di una campagna conclusa si pubblica e si segna (CA-76)."""
    campagna = campagna_attiva(db)
    conclusa = campagna_conclusa(db, profilo_id=campagna.profilo_id)
    vecchia = campagne.foto_della_campagna(db, conclusa.id)[0]
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    [legame] = post.versione_corrente.legami_foto
    # Il post usa la foto d'archivio al posto di quella della campagna.
    altra_id = legame.foto_id
    legame.foto_id = vecchia.id
    _archivia_foto(db, archivio, campagna.id)
    archivio._archivio[vecchia.file] = b"foto-d-archivio"

    pubblica_dovuti(db, ADESSO)

    db.refresh(post)
    assert post.stato == "pubblicato"
    assert len(social.pubblicazioni) == 1
    assert vecchia.pubblicata_su == {"instagram": ADESSO.isoformat()}
    # La foto della campagna rimasta fuori dalla versione non si segna.
    assert db.get(Foto, altra_id).pubblicata_su == {}


def test_ca76_foto_di_gruppo_archivio_si_pubblica_e_si_segna(db, social, archivio):
    """Anche una foto senza campagna (gruppo d'archivio) si pubblica (CA-76)."""
    campagna = campagna_attiva(db)
    mazzo = gruppo_di_archivio(db, profilo_id=campagna.profilo_id, n_foto=1)
    [vecchia] = mazzo.foto
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    [legame] = post.versione_corrente.legami_foto
    legame.foto_id = vecchia.id
    _archivia_foto(db, archivio, campagna.id)
    archivio._archivio[vecchia.file] = b"foto-d-archivio"

    pubblica_dovuti(db, ADESSO)

    db.refresh(post)
    assert post.stato == "pubblicato"
    assert vecchia.campagna_id is None
    assert vecchia.pubblicata_su == {"instagram": ADESSO.isoformat()}


def test_cartolina_pubblicata_non_segna_la_foto(db, social, archivio):
    """La cartolina esce sul canale ma non è caricata: non si segna (R-27)."""
    campagna = campagna_attiva(db)
    post = post_approvato(
        db, campagna_id=campagna.id, data_ora=PASSATO, riempitivo="cartolina"
    )
    cartolina = foto(db, campagna=campagna, origine="cartolina")
    [legame] = post.versione_corrente.legami_foto
    legame.foto_id = cartolina.id
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)

    db.refresh(post)
    assert post.stato == "pubblicato"
    assert len(social.pubblicazioni) == 1
    db.refresh(cartolina)
    assert cartolina.pubblicata_su == {}


def test_ca36_due_tick_una_sola_scrittura_sulla_foto(db, social, archivio):
    """Il secondo tick non ripubblica e non riscrive ``pubblicata_su``."""
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    [legame] = post.versione_corrente.legami_foto
    _archivia_foto(db, archivio, campagna.id)

    pubblica_dovuti(db, ADESSO)
    pubblica_dovuti(db, ADESSO + timedelta(hours=1))

    immagine = db.get(Foto, legame.foto_id)
    assert immagine.pubblicata_su == {"instagram": ADESSO.isoformat()}
    assert len(social.pubblicazioni) == 1


def test_ripresa_dopo_tentativo_rimasto_in_corso(db, social, archivio):
    """Un tentativo in_corso (crash o errore temporaneo) viene ripreso."""
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id, data_ora=PASSATO)
    _archivia_foto(db, archivio, campagna.id)
    # Simula un tentativo interrotto: riga in_corso senza esito.
    db.add(
        Pubblicazione(
            post_id=post.id,
            versione_id=post.versione_corrente.id,
            n_tentativo=1,
            stato="in_corso",
        )
    )
    db.flush()

    pubblica_dovuti(db, ADESSO)

    [tentativo] = _pubblicazioni(db, post.id)
    assert tentativo.stato == "ok"
    assert tentativo.n_tentativo == 2
    db.refresh(post)
    assert post.stato == "pubblicato"
