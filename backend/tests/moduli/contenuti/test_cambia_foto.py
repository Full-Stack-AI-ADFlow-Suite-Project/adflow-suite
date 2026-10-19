"""T3-62: cambia la foto di un post con un'altra del gruppo (spec R-36, CA-71)."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.core.errori import DatiNonValidi, StatoNonValido
from app.moduli.campagne.models import Foto
from app.moduli.contenuti.models import VersionePostFoto
from app.moduli.contenuti.service import cambia_foto, foto_possibili
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.campagne.fabbrica import (
    ANALISI_IDONEA,
    campagna_in_revisione,
    foto as fabbrica_foto,
    gruppo as fabbrica_gruppo,
)
from tests.moduli.contenuti.fabbrica import post_da_approvare

# I post della fabbrica escono il 5/1/2030 alle 12:00 UTC.
ADESSO = datetime(2030, 1, 5, 9, tzinfo=timezone.utc)


def _idonea(una, punteggio):
    una.analisi_ai = {**ANALISI_IDONEA, "punteggio": punteggio}


def _scena(db):
    """Campagna in revisione con 4 foto in un gruppo e un post sulla prima."""
    campagna = campagna_in_revisione(db)
    foto = list(
        db.scalars(
            select(Foto).where(Foto.campagna_id == campagna.id).order_by(Foto.id)
        )
    )
    post = post_da_approvare(db, campagna_id=campagna.id)
    assert post.versione_corrente.legami_foto[0].foto_id == foto[0].id
    return campagna, foto, post


def _ids(elenco):
    return [una.id for una in elenco]


def test_ca71_foto_possibili_del_gruppo_idonee_e_libere_sul_canale(db):
    _, foto, post = _scena(db)
    for una, punteggio in zip(foto, (0.9, 0.5, 0.7, 0.6)):
        _idonea(una, punteggio)
    # Per punteggio decrescente; la foto del post non c'è.
    assert _ids(foto_possibili(db, post.id, ADESSO)) == [
        foto[2].id,
        foto[3].id,
        foto[1].id,
    ]


def test_ca71_foto_senza_analisi_in_cima(db):
    _, foto, post = _scena(db)
    _idonea(foto[2], 0.9)
    _idonea(foto[3], 0.4)
    assert foto[1].analisi_ai is None
    assert _ids(foto_possibili(db, post.id, ADESSO)) == [
        foto[1].id,
        foto[2].id,
        foto[3].id,
    ]


def test_ca71_foto_non_idonea_o_di_un_altro_gruppo_esclusa(db):
    campagna, foto, post = _scena(db)
    foto[1].analisi_ai = {**ANALISI_IDONEA, "idonea": False}
    foto[2].origine = "creata_ai"
    altro = fabbrica_foto(db, gruppo=fabbrica_gruppo(db, campagna))
    _idonea(altro, 0.99)
    assert _ids(foto_possibili(db, post.id, ADESSO)) == [foto[3].id]


def test_ca71_foto_gia_in_un_post_vivo_dello_stesso_canale_esclusa(db):
    campagna, foto, post = _scena(db)
    stesso_canale = post_da_approvare(db, campagna_id=campagna.id, canale="instagram")
    altro_canale = post_da_approvare(db, campagna_id=campagna.id, canale="facebook")
    usata_qui = stesso_canale.versione_corrente.legami_foto[0].foto_id
    usata_altrove = altro_canale.versione_corrente.legami_foto[0].foto_id
    assert len({foto[0].id, usata_qui, usata_altrove}) == 3
    possibili = _ids(foto_possibili(db, post.id, ADESSO))
    assert usata_qui not in possibili
    # Su un altro canale la stessa foto può uscire.
    assert usata_altrove in possibili


def test_ca71_foto_di_un_post_scartato_torna_libera(db):
    campagna, _, post = _scena(db)
    scartato = post_da_approvare(db, campagna_id=campagna.id, stato="scartato")
    liberata = scartato.versione_corrente.legami_foto[0].foto_id
    assert liberata in _ids(foto_possibili(db, post.id, ADESSO))


def test_ca71_nasce_la_versione_cambio_foto_con_lo_stesso_testo(db):
    _, foto, post = _scena(db)
    operatore = utente(db, "operatore")
    post.controllato_da = operatore.id
    post.controllato_il = ADESSO
    post.da_rivedere = True
    prima = post.versione_corrente
    prima.errori_validazione = [{"regola": "r", "livello": "avviso", "messaggio": "m"}]
    prima_utilizzi = foto[2].n_utilizzi

    nuova = cambia_foto(db, post.id, foto[2].id, operatore.id, ADESSO)

    assert post.versione_corrente is nuova
    assert (nuova.numero, nuova.tipo_intervento, nuova.autore_id) == (
        2,
        "cambio_foto",
        operatore.id,
    )
    assert (nuova.testo, nuova.hashtag) == (prima.testo, prima.hashtag)
    assert nuova.errori_validazione == prima.errori_validazione
    assert [(l.posizione, l.foto_id) for l in nuova.legami_foto] == [(1, foto[2].id)]
    # La precedente resta com'è (R-02); spunta caduta, indicatore e cicli invariati.
    assert [(l.posizione, l.foto_id) for l in prima.legami_foto] == [(1, foto[0].id)]
    assert (post.controllato_da, post.controllato_il) == (None, None)
    assert post.da_rivedere is True
    assert post.n_rigenerazioni_testo == 0
    db.refresh(foto[2])
    assert foto[2].n_utilizzi == prima_utilizzi + 1


def test_ca71_in_un_carosello_cambia_la_prima_e_copia_le_altre(db):
    _, foto, post = _scena(db)
    db.add(
        VersionePostFoto(
            versione_id=post.versione_corrente.id, posizione=2, foto_id=foto[3].id
        )
    )
    db.flush()
    db.expire(post.versione_corrente, ["legami_foto"])
    nuova = cambia_foto(db, post.id, foto[1].id, utente(db, "operatore").id, ADESSO)
    assert [(l.posizione, l.foto_id) for l in nuova.legami_foto] == [
        (1, foto[1].id),
        (2, foto[3].id),
    ]


def test_ca71_foto_fuori_elenco_422(db):
    campagna, foto, post = _scena(db)
    altro = fabbrica_foto(db, gruppo=fabbrica_gruppo(db, campagna))
    for sbagliata in (foto[0].id, altro.id, 99999):
        with pytest.raises(DatiNonValidi):
            cambia_foto(db, post.id, sbagliata, utente(db, "operatore").id, ADESSO)
    assert len(post.versioni) == 1


def test_ca71_immagine_ai_409(db):
    campagna, _, _ = _scena(db)
    immagine_ai = post_da_approvare(
        db, campagna_id=campagna.id, canale="facebook", riempitivo="immagine_ai"
    )
    with pytest.raises(StatoNonValido, match="immagine AI non cambia foto"):
        foto_possibili(db, immagine_ai.id, ADESSO)
    with pytest.raises(StatoNonValido):
        cambia_foto(db, immagine_ai.id, 1, utente(db, "operatore").id, ADESSO)


def test_ca71_senza_gruppo_409(db):
    campagna, _, post = _scena(db)
    from app.moduli.contenuti.models import Uscita

    db.get(Uscita, post.uscita_id).gruppo_id = None
    db.flush()
    with pytest.raises(StatoNonValido, match="immagine AI non cambia foto"):
        foto_possibili(db, post.id, ADESSO)
