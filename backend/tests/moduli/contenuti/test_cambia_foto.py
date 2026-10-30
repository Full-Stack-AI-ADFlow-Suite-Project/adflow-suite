"""T3-62, T3-909: cambia la foto del post (spec R-36, CA-71, CA-104, CA-105).

Le foto vengono, in quest'ordine, dal gruppo dell'uscita, dalle altre foto
della campagna e dall'archivio della bottega (ADR-119).
"""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.coda import RIGENERA_POST
from app.core.errori import DatiNonValidi, StatoNonValido
from app.moduli.campagne.models import Foto
from app.moduli.contenuti import interventi
from app.moduli.contenuti.domain import DICITURA_IMMAGINE_AI
from app.moduli.contenuti.models import Uscita, VersionePostFoto
from app.moduli.contenuti.service import cambia_foto, foto_possibili
from app.moduli.revisione import interventi as revisione_interventi
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.campagne.fabbrica import (
    ANALISI_IDONEA,
    campagna_attiva,
    campagna_conclusa,
    campagna_in_revisione,
    foto as fabbrica_foto,
    gruppo as fabbrica_gruppo,
)
from tests.moduli.contenuti.fabbrica import post_approvato, post_da_approvare

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
    return [una.foto.id for una in elenco]


def _voci(elenco):
    return [(una.foto.id, una.provenienza) for una in elenco]


def test_ca71_foto_possibili_del_gruppo_idonee_e_libere_sul_canale(db):
    _, foto, post = _scena(db)
    for una, punteggio in zip(foto, (0.9, 0.5, 0.7, 0.6)):
        _idonea(una, punteggio)
    # Per punteggio decrescente; la foto del post non c'è.
    assert _voci(foto_possibili(db, post.id, ADESSO)) == [
        (foto[2].id, "gruppo"),
        (foto[3].id, "gruppo"),
        (foto[1].id, "gruppo"),
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


def test_ca71_foto_non_idonea_esclusa_e_creata_ai_esclusa(db):
    campagna, foto, post = _scena(db)
    foto[1].analisi_ai = {**ANALISI_IDONEA, "idonea": False}
    foto[2].origine = "creata_ai"
    possibili = _ids(foto_possibili(db, post.id, ADESSO))
    assert foto[1].id not in possibili
    assert foto[2].id not in possibili
    assert foto[3].id in possibili


def test_ca104_le_foto_di_un_altro_gruppo_sono_della_campagna(db):
    """CA-104: le altre foto della campagna arrivano dopo quelle dell'uscita."""
    campagna, foto, post = _scena(db)
    _idonea(foto[1], 0.9)
    _idonea(foto[2], 0.4)
    _idonea(foto[3], 0.8)
    altro = fabbrica_foto(db, gruppo=fabbrica_gruppo(db, campagna))
    _idonea(altro, 0.99)

    voci = _voci(foto_possibili(db, post.id, ADESSO))
    # Prima il gruppo dell'uscita (per punteggio), poi il resto della campagna.
    assert voci[:3] == [
        (foto[1].id, "gruppo"),
        (foto[3].id, "gruppo"),
        (foto[2].id, "gruppo"),
    ]
    assert (altro.id, "campagna") in voci


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
    prima_utilizzi = foto[2].n_utilizzi

    nuova = cambia_foto(db, post.id, foto[2].id, operatore.id, ADESSO)

    assert post.versione_corrente is nuova
    assert (nuova.numero, nuova.tipo_intervento, nuova.autore_id) == (
        2,
        "cambio_foto",
        operatore.id,
    )
    assert (nuova.testo, nuova.hashtag) == (prima.testo, prima.hashtag)
    # Gli errori del validatore si ricalcolano sul testo nuovo.
    assert nuova.errori_validazione == []
    assert [(l.posizione, l.foto_id) for l in nuova.legami_foto] == [(1, foto[2].id)]
    # La precedente resta com'è (R-02); spunta caduta, indicatore e cicli invariati.
    assert [(l.posizione, l.foto_id) for l in prima.legami_foto] == [(1, foto[0].id)]
    assert (post.controllato_da, post.controllato_il) == (None, None)
    assert post.da_rivedere is False
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
    non_idonea = foto[1]
    non_idonea.analisi_ai = {**ANALISI_IDONEA, "idonea": False}
    for sbagliata in (foto[0].id, non_idonea.id, 99999):
        with pytest.raises(DatiNonValidi):
            cambia_foto(db, post.id, sbagliata, utente(db, "operatore").id, ADESSO)
    assert len(post.versioni) == 1


def test_ca104_l_archivio_arriva_dopo_la_campagna_con_la_sua_provenienza(db):
    """CA-104: le foto di `foto_di_archivio()` chiudono l'elenco."""
    campagna, foto, post = _scena(db)
    chiusa = campagna_conclusa(db, profilo_id=campagna.profilo_id)
    di_archivio = list(
        db.scalars(select(Foto).where(Foto.campagna_id == chiusa.id).order_by(Foto.id))
    )
    assert di_archivio

    voci = _voci(foto_possibili(db, post.id, ADESSO))
    assert all(provenienza == "archivio" for _, provenienza in voci[-4:])
    assert [una.id for una in di_archivio] == [una for una, _ in voci[-4:]]
    # Nessun doppione.
    assert len(_ids(foto_possibili(db, post.id, ADESSO))) == len(voci)


def test_ca104_il_soggetto_viene_dall_analisi(db):
    """CA-104: `soggetto` è quello dell'analisi, se c'è."""
    _, foto, post = _scena(db)
    foto[1].analisi_ai = {**ANALISI_IDONEA, "punteggio": 0.5, "soggetto": "una brocca"}
    voce = next(
        una
        for una in interventi.foto_possibili(db, post.id, ADESSO)
        if una.foto.id == foto[1].id
    )
    assert (voce.foto.analisi_ai or {}).get("soggetto") == "una brocca"


def test_ca104_un_post_con_immagine_ai_cambia_con_una_foto_vera(db):
    """CA-104: ammesso sui post con un'immagine AI; il testo perde la dicitura."""
    campagna, foto, post = _scena(db)
    db.get(Uscita, post.uscita_id).gruppo_id = None
    post.riempitivo = "immagine_ai"
    post.versione_corrente.testo = f"Testo di prova\n\n{DICITURA_IMMAGINE_AI}"
    db.flush()

    possibili = foto_possibili(db, post.id, ADESSO)
    assert possibili
    assert all(una.provenienza == "campagna" for una in possibili)

    nuova = cambia_foto(
        db, post.id, possibili[0].foto.id, utente(db, "operatore").id, ADESSO
    )

    assert nuova.testo == "Testo di prova"
    assert post.riempitivo is None


def test_ca105_riscrivi_testo_accende_l_intervento_e_accoda_il_job(db, coda):
    """CA-105: cambio foto + riscrivi testo → `rigenera_totale` e `rigenera_post`."""
    _, foto, post = _scena(db)
    operatore = utente(db, "operatore")

    nuova = revisione_interventi.cambia_foto(
        db,
        post.id,
        foto[2].id,
        operatore,
        ADESSO,
        riscrivi_testo=True,
        nota="tono più caldo",
    )

    assert nuova.tipo_intervento == "cambio_foto"
    assert post.intervento_in_corso == "rigenera_totale"
    assert post.intervento_dal == ADESSO
    [job] = coda.jobs.values()
    assert job["task_name"] == RIGENERA_POST
    assert job["args"] == {
        "post_id": post.id,
        "testo_proposto": None,
        "nota": "tono più caldo",
    }


def test_ca105_senza_cicli_rimasti_409_e_nessuna_versione(db):
    """CA-105: senza rigenerazioni del testo rimaste, 409 prima di cambiare."""
    _, foto, post = _scena(db)
    post.n_rigenerazioni_testo = 3
    db.flush()

    with pytest.raises(StatoNonValido, match="non si può più rigenerare"):
        revisione_interventi.cambia_foto(
            db,
            post.id,
            foto[2].id,
            utente(db, "operatore"),
            ADESSO,
            riscrivi_testo=True,
        )
    assert len(post.versioni) == 1


def test_ca105_dopo_l_approvazione_riscrivi_testo_422(db):
    """CA-105: dopo l'approvazione il testo si riscrive solo a mano."""
    campagna = campagna_attiva(db)
    post = post_approvato(
        db, campagna_id=campagna.id, data_ora=ADESSO + timedelta(hours=1)
    )
    scelta = foto_possibili(db, post.id, ADESSO)[0].foto

    with pytest.raises(DatiNonValidi, match="Dopo l'approvazione"):
        revisione_interventi.cambia_foto(
            db,
            post.id,
            scelta.id,
            utente(db, "operatore"),
            ADESSO,
            riscrivi_testo=True,
        )
    assert len(post.versioni) == 1
