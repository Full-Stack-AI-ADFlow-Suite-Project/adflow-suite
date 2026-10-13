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
    "limite_login",
    "notifica",
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
    "versione_foto",
    "anagrafica_artigiano",
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
    command.downgrade(config, "011")
    with motore_test.begin() as conn:
        utente_id = conn.execute(
            text(
                "insert into utente(email,password_hash,nome,ruolo) "
                "values ('migrazione-t3@example.test','hash','Artigiano','artigiano') "
                "returning id"
            )
        ).scalar_one()
        profilo_id = conn.execute(
            text(
                "insert into profilo_bottega(utente_id,nome,referente,citta,"
                "tipo_prodotto,clienti_ideali,obiettivo,canali) values "
                "(:utente,'Bottega','Referente','Roma','altro','Clienti',"
                "'notorieta',array['instagram']) returning id"
            ),
            {"utente": utente_id},
        ).scalar_one()
        campagna_id = conn.execute(
            text(
                "insert into campagna(profilo_id,titolo,inizio,fine,stato) "
                "values (:profilo,'Migrazione',date '2030-01-01',"
                "date '2030-01-07','in_revisione') returning id"
            ),
            {"profilo": profilo_id},
        ).scalar_one()
        gruppo_id = conn.execute(
            text(
                "insert into gruppo_foto(profilo_id,campagna_id,origine) "
                "values (:profilo,:campagna,'caricate') returning id"
            ),
            {"profilo": profilo_id, "campagna": campagna_id},
        ).scalar_one()
        foto_id = conn.execute(
            text(
                "insert into foto(profilo_id,campagna_id,gruppo_id,file,mime,"
                "larghezza,altezza) values (:profilo,:campagna,:gruppo,"
                "'originale.jpg','image/jpeg',1080,1350) returning id"
            ),
            {"profilo": profilo_id, "campagna": campagna_id, "gruppo": gruppo_id},
        ).scalar_one()
        uscita_id = conn.execute(
            text(
                "insert into uscita(campagna_id,numero,tema) "
                "values (:campagna,1,'Tema') returning id"
            ),
            {"campagna": campagna_id},
        ).scalar_one()
        post_id = conn.execute(
            text(
                "insert into post(campagna_id,uscita_id,canale,data_ora,stato) "
                "values (:campagna,:uscita,'instagram',"
                "timestamptz '2030-01-02 10:00:00+00','da_approvare') returning id"
            ),
            {"campagna": campagna_id, "uscita": uscita_id},
        ).scalar_one()
        versione_id = conn.execute(
            text(
                "insert into versione_post(post_id,numero,testo,hashtag,"
                "tipo_intervento) values (:post,1,'Testo',array[]::text[],'generazione') "
                "returning id"
            ),
            {"post": post_id},
        ).scalar_one()
        conn.execute(
            text(
                "insert into versione_post_foto(versione_id,posizione,foto_id) "
                "values (:versione,1,:foto)"
            ),
            {"versione": versione_id, "foto": foto_id},
        )
    command.upgrade(config, "head")
    with motore_test.connect() as conn:
        originale = conn.execute(
            text(
                "select v.id,v.numero,v.file,v.origine,l.versione_foto_id "
                "from versione_foto v join versione_post_foto l "
                "on l.foto_id=v.foto_id where v.foto_id=:foto and v.numero=0"
            ),
            {"foto": foto_id},
        ).one()
        assert (originale.numero, originale.file, originale.origine) == (
            0,
            "originale.jpg",
            "originale",
        )
        assert originale.versione_foto_id == originale.id
    command.downgrade(config, "011")
    with motore_test.connect() as conn:
        tabelle = set(inspect(conn).get_table_names())
        assert not {"versione_foto", "anagrafica_artigiano"} & tabelle
        assert "notifica" in tabelle
        assert "n_ritocchi_foto" not in {
            c["name"] for c in inspect(conn).get_columns("post")
        }
        assert "versione_foto_id" not in {
            c["name"] for c in inspect(conn).get_columns("versione_post_foto")
        }
    with motore_test.begin() as conn:
        conn.execute(
            text(
                "delete from versione_post_foto where versione_id in "
                "(select id from versione_post where post_id in "
                "(select id from post where campagna_id=:campagna))"
            ),
            {"campagna": campagna_id},
        )
        conn.execute(
            text(
                "delete from versione_post where post_id in (select id from post where campagna_id=:id)"
            ),
            {"id": campagna_id},
        )
        conn.execute(
            text("delete from post where campagna_id=:id"), {"id": campagna_id}
        )
        conn.execute(
            text("delete from uscita where campagna_id=:id"), {"id": campagna_id}
        )
        conn.execute(
            text("delete from foto where campagna_id=:id"), {"id": campagna_id}
        )
        conn.execute(
            text("delete from gruppo_foto where campagna_id=:id"), {"id": campagna_id}
        )
        conn.execute(text("delete from campagna where id=:id"), {"id": campagna_id})
        conn.execute(
            text("delete from profilo_bottega where id=:id"), {"id": profilo_id}
        )
        conn.execute(text("delete from utente where id=:id"), {"id": utente_id})
    command.downgrade(config, "010")
    with motore_test.connect() as conn:
        assert "notifica" not in inspect(conn).get_table_names()
        assert "pubblicata_su" in {c["name"] for c in inspect(conn).get_columns("foto")}
    command.downgrade(config, "009")
    with motore_test.connect() as conn:
        colonne = {c["name"] for c in inspect(conn).get_columns("foto")}
        assert "pubblicata_su" not in colonne
        assert "limite_login" in inspect(conn).get_table_names()
    command.downgrade(config, "008")
    with motore_test.connect() as conn:
        assert "limite_login" not in inspect(conn).get_table_names()
        assert TABELLE_NUOVE_008 <= set(inspect(conn).get_table_names())
    command.downgrade(config, "007")
    with motore_test.connect() as conn:
        assert not TABELLE_NUOVE_008 & set(inspect(conn).get_table_names())
    command.downgrade(config, "006")
    with motore_test.connect() as conn:
        assert not TABELLE_CODA & set(inspect(conn).get_table_names())
    command.downgrade(config, "005")
    with motore_test.connect() as conn:
        assert "pubblicazione" not in inspect(conn).get_table_names()
    command.upgrade(config, "head")
    with motore_test.connect() as conn:
        assert (
            set(inspect(conn).get_table_names()) - {"alembic_version"}
            == TABELLE | TABELLE_CODA
        )
        assert conn.scalar(text("select version_num from alembic_version")) == "012"
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
