"""T1-03: migrazioni e vincoli verificati su PostgreSQL reale."""
from datetime import datetime, timezone
from hashlib import sha256

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.tabelle import del_modello, metadata
from app.moduli.accesso.models import Sessione
from app.moduli.campagne.models import DecisioneCampagna, GruppoFoto
from app.moduli.contenuti.models import VersionePost
from app.moduli.revisione.models import Approvazione
from app.moduli.pubblicazione.models import Pubblicazione
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_in_bozza,
    campagna_inviata,
    campagna_in_revisione,
    campagna_attiva,
    foto,
)
from tests.moduli.contenuti.fabbrica import post_da_approvare, post_approvato

TABELLE = {
    "utente",
    "sessione",
    "profilo_bottega",
    "account_social",
    "campagna",
    "gruppo_foto",
    "foto",
    "decisione_campagna",
    "piano",
    "uscita",
    "post",
    "versione_post",
    "versione_post_foto",
    "errore_generazione",
    "approvazione",
    "pubblicazione",
}
TABELLE_NUOVE_008 = {
    "account_social",
    "gruppo_foto",
    "piano",
    "uscita",
    "versione_post_foto",
    "errore_generazione",
}
TABELLE_CODA = {
    "procrastinate_jobs",
    "procrastinate_events",
    "procrastinate_periodic_defers",
    "procrastinate_workers",
}


def test_upgrade_downgrade_completo_e_ultimo_passaggio(motore_test):
    config = Config("alembic.ini")
    config.attributes["url"] = motore_test.url.render_as_string(hide_password=False)
    command.downgrade(config, "base")
    with motore_test.connect() as conn:
        assert set(inspect(conn).get_table_names()) - {"alembic_version"} == set()
        assert not conn.scalar(
            text(
                "select count(*) from (select proname from pg_proc union all"
                " select typname from pg_type) nomi(nome)"
                " where nome like 'procrastinate%'"
            )
        )
    command.upgrade(config, "head")
    command.downgrade(config, "-1")
    with motore_test.connect() as conn:
        assert not TABELLE_NUOVE_008 & set(inspect(conn).get_table_names())
    command.downgrade(config, "-1")
    with motore_test.connect() as conn:
        assert not TABELLE_CODA & set(inspect(conn).get_table_names())
    command.downgrade(config, "-1")
    with motore_test.connect() as conn:
        assert "pubblicazione" not in inspect(conn).get_table_names()
    command.upgrade(config, "head")
    with motore_test.connect() as conn:
        assert (
            set(inspect(conn).get_table_names()) - {"alembic_version"}
            == TABELLE | TABELLE_CODA
        )
        assert conn.scalar(text("select version_num from alembic_version")) == "008"
        contesto = MigrationContext.configure(conn, opts={"include_name": del_modello})
        assert compare_metadata(contesto, metadata) == []


def test_email_unica(db):
    primo = utente(db)
    with pytest.raises(IntegrityError), db.begin_nested():
        utente(db, email=primo.email)
    assert db.get(type(primo), primo.id) is not None


def test_profilo_unico_per_utente(db):
    primo = profilo(db)
    with pytest.raises(IntegrityError), db.begin_nested():
        profilo(db, utente_id=primo.utente_id)


def test_fk_utente_inesistente(db):
    with pytest.raises(IntegrityError), db.begin_nested():
        profilo(db, utente_id=-1)


def test_profilo_campi_obbligatori(db):
    with pytest.raises(IntegrityError), db.begin_nested():
        profilo(db, nome=None)


def test_sessione_token_unico_e_scadenza_utc(db):
    record = utente(db)
    digest = sha256(b"token-solo-test").hexdigest()
    scadenza = datetime(2030, 1, 1, tzinfo=timezone.utc)
    sessione = Sessione(utente_id=record.id, token_hash=digest, scade_il=scadenza)
    db.add(sessione)
    db.flush()
    db.expire(sessione)
    assert sessione.scade_il == scadenza
    assert sessione.token_hash == digest
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(Sessione(utente_id=record.id, token_hash=digest, scade_il=scadenza))
        db.flush()


def test_roundtrip_json_array_e_default(db):
    campagna = campagna_inviata(
        db,
        profilo_snapshot={
            "nome": "Bottega",
            "valori": ["tradizione"],
            "social_esistenti": {"canali": ["instagram"]},
        },
    )
    mazzo = db.scalar(select(GruppoFoto).where(GruppoFoto.campagna_id == campagna.id))
    immagine = foto(db, gruppo=mazzo)
    db.expire_all()
    assert campagna.profilo_snapshot["social_esistenti"]["canali"] == ["instagram"]
    assert campagna.canali == ["instagram"]
    assert campagna.canali_tolti is None
    assert campagna.chiusa_il is None
    assert mazzo.origine == "caricate"
    assert mazzo.descrizione
    assert immagine.gruppo_id == mazzo.id
    assert immagine.campagna_id == campagna.id
    assert immagine.origine == "caricata"
    assert immagine.da_usare is False
    assert immagine.n_utilizzi == 0


def test_numero_versione_unico_per_post(db):
    post = post_da_approvare(db)
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(
            VersionePost(
                post_id=post.id,
                numero=1,
                testo="Duplicato",
                hashtag=[],
                tipo_intervento="generazione",
                provider_ai="finto",
                modello_ai="finto",
                versione_prompt="1",
            )
        )
        db.flush()


def test_secondo_ok_stesso_post_rifiutato_ma_errori_ammessi(db):
    post = post_approvato(db)
    versione = db.scalar(select(VersionePost).where(VersionePost.post_id == post.id))
    for numero, stato in enumerate(["errore", "errore", "ok"], 1):
        db.add(
            Pubblicazione(
                post_id=post.id,
                versione_id=versione.id,
                n_tentativo=numero,
                stato=stato,
            )
        )
    db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(
            Pubblicazione(
                post_id=post.id, versione_id=versione.id, n_tentativo=4, stato="ok"
            )
        )
        db.flush()
    altro = post_approvato(db)
    altra_versione = db.scalar(
        select(VersionePost).where(VersionePost.post_id == altro.id)
    )
    db.add(
        Pubblicazione(
            post_id=altro.id, versione_id=altra_versione.id, n_tentativo=1, stato="ok"
        )
    )
    db.flush()


def test_stesso_numero_di_tentativo_rifiutato(db):
    post = post_approvato(db)
    versione = db.scalar(select(VersionePost).where(VersionePost.post_id == post.id))
    db.add(
        Pubblicazione(
            post_id=post.id, versione_id=versione.id, n_tentativo=1, stato="in_corso"
        )
    )
    db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(
            Pubblicazione(
                post_id=post.id,
                versione_id=versione.id,
                n_tentativo=1,
                stato="in_corso",
            )
        )
        db.flush()


def test_versione_senza_dati_ai_ammessa(db):
    post = post_da_approvare(db)
    db.add(
        VersionePost(
            post_id=post.id,
            numero=2,
            testo="Stesso testo, altra foto",
            hashtag=[],
            tipo_intervento="scelta_foto",
        )
    )
    db.flush()


def test_aggiornamento_a_secondo_ok_rifiutato(db):
    post = post_approvato(db)
    versione = db.scalar(select(VersionePost).where(VersionePost.post_id == post.id))
    db.add(
        Pubblicazione(
            post_id=post.id, versione_id=versione.id, n_tentativo=1, stato="ok"
        )
    )
    secondo = Pubblicazione(
        post_id=post.id, versione_id=versione.id, n_tentativo=2, stato="errore"
    )
    db.add(secondo)
    db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():
        secondo.stato = "ok"
        db.flush()


def test_decisione_e_approvazione_persistono(db):
    post = post_da_approvare(db)
    operatore = utente(db, "operatore")
    versione = db.scalar(select(VersionePost).where(VersionePost.post_id == post.id))
    decisione = DecisioneCampagna(
        campagna_id=post.campagna_id,
        utente_id=operatore.id,
        esito="approvata",
        foto_segnate=[],
    )
    approvazione = Approvazione(
        versione_id=versione.id,
        utente_id=operatore.id,
        ruolo="operatore",
        esito="approvata",
    )
    db.add_all([decisione, approvazione])
    db.flush()
    db.expire_all()
    assert decisione.esito == approvazione.esito == "approvata"
    assert decisione.creata_il.utcoffset().total_seconds() == 0


@pytest.mark.parametrize(
    "fabbrica,stato",
    [
        (campagna_in_bozza, "bozza"),
        (campagna_inviata, "inviata"),
        (campagna_in_revisione, "in_revisione"),
        (campagna_attiva, "attiva"),
    ],
)
def test_fabbriche_indipendenti(db, fabbrica, stato):
    primo = fabbrica(db)
    secondo = fabbrica(db)
    assert primo.id != secondo.id
    assert primo.profilo_id != secondo.profilo_id
    assert primo.stato == secondo.stato == stato


def test_fabbriche_non_fanno_commit(motore_test):
    with motore_test.connect() as conn:
        transazione = conn.begin()
        with Session(conn, join_transaction_mode="create_savepoint") as sessione:
            record = utente(sessione)
            identificatore = record.id
        transazione.rollback()
    with motore_test.connect() as conn:
        assert (
            conn.scalar(
                text("select count(*) from utente where id=:id"), {"id": identificatore}
            )
            == 0
        )
