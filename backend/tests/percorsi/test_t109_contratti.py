"""T1-09: contratti condivisi e criteri di accettazione su PostgreSQL."""

from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import Depends
from pydantic import ValidationError
from sqlalchemy import func, select

from app import cli, main
from app.core.config import Impostazioni
from app.core.errori import DatiNonValidi, NonTrovato, StatoNonValido
from app.moduli.accesso.service import richiede_ruolo
from app.moduli.artigiani import domain as artigiani_domain
from app.moduli.artigiani.models import AccountSocial
from app.moduli.artigiani.service import canali_collegati, profilo_di
from app.moduli.campagne import domain as campagne_domain
from app.moduli.campagne import service as campagne
from app.moduli.campagne.models import DecisioneCampagna
from app.moduli.contenuti import domain as contenuti_domain
from app.moduli.contenuti import service as contenuti
from app.moduli.contenuti.models import (
    ErroreGenerazione,
    VersionePost,
    VersionePostFoto,
)
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import account_social, profilo
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_con_piano_da_rivedere,
    campagna_in_bozza,
    campagna_in_revisione,
    campagna_inviata,
    foto,
    gruppo,
)
from tests.moduli.contenuti.fabbrica import piano, post_da_approvare, uscita

ORA = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize("stato", ["collegato", "scaduto", "scollegato"])
def test_canali_collegati_filtra_per_profilo_e_stato(db, stato):
    bottega = profilo(db, canali=["facebook", "instagram"])
    facebook = db.scalar(
        select(AccountSocial).where(
            AccountSocial.profilo_id == bottega.id,
            AccountSocial.piattaforma == "facebook",
        )
    )
    facebook.stato = stato
    profilo(db, canali=["facebook", "instagram"])
    assert canali_collegati(db, bottega.id) == (
        ["facebook", "instagram"] if stato == "collegato" else ["instagram"]
    )
    assert canali_collegati(db, -1) == []


@pytest.mark.parametrize("piattaforma", ["facebook", "instagram"])
def test_fabbrica_account_senza_profilo_non_duplica(db, piattaforma):
    record = account_social(db, piattaforma=piattaforma, stato="scaduto")
    assert record.piattaforma == piattaforma
    assert record.stato == "scaduto"


def test_gruppi_caricano_le_foto_e_escludono_archivio_e_altre_campagne(db):
    campagna = campagna_inviata(db)
    secondo = gruppo(db, campagna, origine="create_ai", n_immagini=2)
    gruppo(db, campagna, campagna_id=None)
    gruppo(db)
    trovati = campagne.gruppi_della_campagna(db, campagna.id)
    assert len(trovati) == 2
    assert len(trovati[0].foto) == 4
    assert trovati[1] is secondo
    assert trovati[1].foto == []
    db.expunge_all()
    assert all(f.gruppo_id == trovati[0].id for f in trovati[0].foto)
    assert campagne.gruppi_della_campagna(db, -1) == []


def test_aggiungi_foto_cartolina_senza_gruppo(db):
    campagna = campagna_inviata(db)
    immagine = campagne.aggiungi_foto(
        db, campagna.id, "cartolina", "cartolina.png", "image/png", 1080, 1350
    )
    db.expire(immagine)
    assert immagine.profilo_id == campagna.profilo_id
    assert immagine.campagna_id == campagna.id
    assert immagine.gruppo_id is None
    assert immagine.origine == "cartolina"
    assert (immagine.file, immagine.mime, immagine.larghezza, immagine.altezza) == (
        "cartolina.png",
        "image/png",
        1080,
        1350,
    )
    assert immagine in campagne.foto_della_campagna(db, campagna.id)


def test_aggiungi_foto_errori(db):
    record = campagna_inviata(db)
    with pytest.raises(DatiNonValidi):
        campagne.aggiungi_foto(
            db, record.id, "inesistente", "x.png", "image/png", 1080, 1080
        )
    with pytest.raises(NonTrovato):
        campagne.aggiungi_foto(db, -1, "cartolina", "x.png", "image/png", 1080, 1080)
    assert len(campagne.foto_della_campagna(db, record.id)) == 4


@pytest.mark.parametrize(
    ("iniziale", "finale"),
    [
        ("in_revisione", "respinta"),
        ("inviata", "scaduta"),
        ("attiva", "annullata"),
        ("attiva", "conclusa"),
    ],
)
def test_cambia_stato_memorizza_la_chiusura_iniettata(db, iniziale, finale):
    record = campagna_in_bozza(db, stato=iniziale)
    campagne.cambia_stato(db, record, finale, ora=ORA)
    db.expire(record)
    assert record.chiusa_il == ORA
    with pytest.raises(StatoNonValido):
        campagne.cambia_stato(db, record, "bozza", ora=ORA + timedelta(days=1))
    assert record.chiusa_il == ORA


def test_cambia_stato_usa_orologio_comune_senza_parametro(db, monkeypatch):
    from app.core import orologio

    monkeypatch.setattr(orologio, "adesso", lambda: ORA)
    record = campagna_attiva(db)
    campagne.cambia_stato(db, record, "conclusa")
    assert record.chiusa_il == ORA


def test_cambia_stato_non_chiude_la_sospensione(db):
    record = campagna_attiva(db)
    campagne.cambia_stato(db, record, "sospesa", ora=ORA)
    campagne.cambia_stato(db, record, "attiva", ora=ORA)
    assert record.chiusa_il is None


@pytest.mark.parametrize(
    "esito",
    [
        "approvata",
        "respinta",
        "proseguita",
        "canale_tolto",
        "nota",
        "sospesa",
        "riattivata",
        "annullata",
        "riprogrammato",
    ],
)
def test_decisioni_nuove_preservano_storico_e_campi(db, esito):
    record = campagna_in_revisione(db)
    operatore = utente(db, "operatore")
    post = post_da_approvare(db, campagna_id=record.id)
    campagne.registra_decisione(
        db, record, operatore.id, "nota", None, "Prima nota", []
    )
    campagne.registra_decisione(
        db,
        record,
        operatore.id,
        esito,
        "altro" if esito == "respinta" else None,
        "Nota",
        [],
        canale="instagram" if esito == "canale_tolto" else None,
        post_id=post.id if esito == "riprogrammato" else None,
    )
    decisioni = db.scalars(
        select(DecisioneCampagna)
        .where(DecisioneCampagna.campagna_id == record.id)
        .order_by(DecisioneCampagna.id)
    ).all()
    assert [d.esito for d in decisioni] == ["nota", esito]
    assert decisioni[-1].canale == ("instagram" if esito == "canale_tolto" else None)
    assert decisioni[-1].post_id == (post.id if esito == "riprogrammato" else None)


def test_rimandata_non_e_piu_un_esito(db):
    record = campagna_in_revisione(db)
    with pytest.raises(DatiNonValidi):
        campagne.registra_decisione(
            db, record, utente(db, "operatore").id, "rimandata", None, "Nota", []
        )


def test_piano_uscite_e_errori_correnti_non_confondono_campagne(db):
    record = campagna_inviata(db)
    assert contenuti.piano_corrente(db, record.id) is None
    assert contenuti.uscite_della_campagna(db, record.id) == []
    assert contenuti.ultimo_errore(db, record.id) is None
    ultimo = piano(db, record, numero=2)
    piano(db, record, numero=1)
    piano(db)
    seconda = uscita(db, record, numero=2)
    prima = uscita(db, record, numero=1)
    uscita(db)
    errori = [
        ErroreGenerazione(
            campagna_id=record.id,
            tipo="temporaneo",
            messaggio="Errore di prova",
            tappa="piano",
            creata_il=istante,
        )
        for istante in [ORA, ORA, ORA - timedelta(days=1)]
    ]
    db.add_all(errori)
    altra = campagna_inviata(db)
    db.add(
        ErroreGenerazione(
            campagna_id=altra.id,
            tipo="configurazione",
            messaggio="Altro",
            tappa="analisi",
            creata_il=ORA + timedelta(days=1),
        )
    )
    db.flush()
    assert contenuti.piano_corrente(db, record.id) is ultimo
    assert contenuti.uscite_della_campagna(db, record.id) == [prima, seconda]
    assert contenuti.ultimo_errore(db, record.id) is errori[1]


def test_foto_di_tutte_le_versioni_ordinate_disponibili_senza_sessione(db):
    record = campagna_in_revisione(db)
    post = post_da_approvare(db, campagna_id=record.id)
    immagini = campagne.foto_della_campagna(db, record.id)
    v2 = VersionePost(
        post_id=post.id,
        numero=2,
        testo="Versione nuova",
        hashtag=[],
        tipo_intervento="modifica_operatore",
    )
    db.add(v2)
    db.flush()
    db.add_all(
        [
            VersionePostFoto(versione_id=v2.id, posizione=2, foto_id=immagini[1].id),
            VersionePostFoto(versione_id=v2.id, posizione=1, foto_id=immagini[0].id),
        ]
    )
    db.flush()
    trovato = contenuti.post_della_campagna(db, record.id)[0]
    db.expunge_all()
    assert len(trovato.versioni[0].foto) == 1
    assert [f.foto_id for f in trovato.versione_corrente.foto] == [
        immagini[0].id,
        immagini[1].id,
    ]


@pytest.mark.parametrize(
    ("minuti", "blocca"), [(0, True), (9.999, True), (10, False), (11, False)]
)
def test_ha_blocchi_intervento_soglia_dieci_minuti(db, minuti, blocca):
    record = campagna_in_revisione(db)
    post = post_da_approvare(
        db,
        campagna_id=record.id,
        intervento_in_corso="rigenera_totale",
        intervento_dal=ORA - timedelta(minutes=minuti),
    )
    assert contenuti.ha_blocchi(db, record.id, ORA) is blocca
    assert post.intervento_in_corso == "rigenera_totale"


@pytest.mark.parametrize(
    "stato", ["approvato", "pubblicato", "fallito", "annullato", "scartato", "scaduto"]
)
def test_ha_blocchi_ignora_post_non_da_approvare(db, stato):
    record = campagna_in_revisione(db)
    post_da_approvare(
        db,
        campagna_id=record.id,
        stato=stato,
        da_rivedere=True,
        intervento_in_corso="rigenera_totale",
        intervento_dal=ORA,
    )
    assert contenuti.ha_blocchi(db, record.id, ORA) is False


def test_approva_scade_passati_lascia_scartati_e_scaduti(db):
    record = campagna_in_revisione(db)
    passato = post_da_approvare(
        db, campagna_id=record.id, data_ora=ORA - timedelta(microseconds=1)
    )
    preciso = post_da_approvare(db, campagna_id=record.id, data_ora=ORA)
    futuro = post_da_approvare(
        db, campagna_id=record.id, data_ora=ORA + timedelta(days=1)
    )
    scartato = post_da_approvare(
        db, campagna_id=record.id, stato="scartato", da_rivedere=True
    )
    scaduto = post_da_approvare(db, campagna_id=record.id, stato="scaduto")
    assert [v.post_id for v in contenuti.approva_post(db, record.id, ORA)] == [
        preciso.id,
        futuro.id,
    ]
    assert passato.stato == "scaduto"
    assert scartato.stato == "scartato"
    assert scaduto.stato == "scaduto"
    assert preciso.stato == futuro.stato == "approvato"


@pytest.mark.parametrize("caso", ["vuota", "solo_passati", "da_rivedere", "intervento"])
def test_approva_errori_non_lasciano_modifiche_parziali(db, caso):
    record = campagna_in_revisione(db)
    post = []
    if caso != "vuota":
        post.append(
            post_da_approvare(
                db, campagna_id=record.id, data_ora=ORA - timedelta(days=1)
            )
        )
    if caso in ("da_rivedere", "intervento"):
        post.append(
            post_da_approvare(
                db,
                campagna_id=record.id,
                da_rivedere=caso == "da_rivedere",
                intervento_in_corso="rigenera_totale" if caso == "intervento" else None,
                intervento_dal=ORA,
            )
        )
    with pytest.raises(StatoNonValido):
        contenuti.approva_post(db, record.id, ORA)
    db.expire_all()
    assert all(p.stato == "da_approvare" for p in post)


def test_avvisi_e_spunte_mancanti_non_bloccano(db):
    record = campagna_in_revisione(db)
    post = post_da_approvare(db, campagna_id=record.id)
    post.versione_corrente.errori_validazione = [
        {"livello": "avviso", "regola": "lunghezza", "messaggio": "Testo lungo"}
    ]
    assert post.controllato_da is None
    assert contenuti.ha_blocchi(db, record.id, ORA) is False
    assert contenuti.approva_post(db, record.id, ORA) == [post.versione_corrente]


@pytest.mark.parametrize("stato", ["pubblicato", "annullato", "scartato", "scaduto"])
def test_ca39_post_chiusi_senza_falliti_non_attendono_fine_periodo(db, stato):
    record = campagna_attiva(db)
    post_da_approvare(db, campagna_id=record.id, stato=stato)
    assert contenuti.tutti_chiusi(db, record.id, ORA) is True


def test_ca39_post_falliti_attendono_fine_periodo_a_roma(db):
    record = campagna_attiva(db, fine=date(2030, 1, 31))
    post_da_approvare(db, campagna_id=record.id, stato="fallito")
    # 23:00 UTC è mezzanotte a Roma in gennaio.
    fine = datetime(2030, 1, 31, 23, tzinfo=timezone.utc)
    assert (
        contenuti.tutti_chiusi(db, record.id, fine - timedelta(microseconds=1)) is False
    )
    assert contenuti.tutti_chiusi(db, record.id, fine) is True
    post_da_approvare(db, campagna_id=record.id, stato="approvato")
    assert contenuti.tutti_chiusi(db, record.id, fine) is False


@pytest.mark.parametrize(
    ("ruolo", "ammesso"), [("artigiano", False), ("operatore", True), ("admin", True)]
)
def test_ca61_admin_passa_come_operatore_ma_non_artigiano(
    client, utente_di_prova, ruolo, ammesso
):
    @main.app.get("/api/_t109/operatore")
    def operatore(utente=Depends(richiede_ruolo("operatore"))):
        return {"ruolo": utente.ruolo}

    @main.app.get("/api/_t109/artigiano")
    def artigiano(utente=Depends(richiede_ruolo("artigiano"))):
        return {"ruolo": utente.ruolo}

    try:
        utente_di_prova(ruolo)
        assert client.get("/api/_t109/operatore").status_code == (
            200 if ammesso else 403
        )
        assert client.get("/api/_t109/artigiano").status_code == (
            200 if ruolo == "artigiano" else 403
        )
    finally:
        main.app.router.routes[:] = [
            r
            for r in main.app.router.routes
            if not getattr(r, "path", "").startswith("/api/_t109/")
        ]


def test_ca63_consorzio_senza_sessione_dalla_configurazione(client, monkeypatch):
    impostazioni = Impostazioni(
        _env_file=None,
        database_url="postgresql://finto",
        database_url_test="postgresql://finto",
        consorzio_nome="Consorzio di prova",
        consorzio_telefono="0123456",
        consorzio_email="contatto@example.test",
    )
    monkeypatch.setattr(main, "leggi_impostazioni", lambda: impostazioni)
    risposta = client.get("/api/consorzio")
    assert risposta.status_code == 200
    assert risposta.json() == {
        "nome": "Consorzio di prova",
        "telefono": "0123456",
        "email": "contatto@example.test",
    }


def test_durate_sessione_default_e_configurabili(monkeypatch):
    for campo in ("SESSIONE_ARTIGIANO_GIORNI", "SESSIONE_OPERATORE_ORE"):
        monkeypatch.delenv(campo, raising=False)
    valori = dict(
        _env_file=None,
        database_url="postgresql://finto",
        database_url_test="postgresql://finto",
    )
    configurazione = Impostazioni(**valori)
    assert (
        configurazione.sessione_artigiano_giorni,
        configurazione.sessione_operatore_ore,
    ) == (7, 12)
    monkeypatch.setenv("SESSIONE_ARTIGIANO_GIORNI", "9")
    monkeypatch.setenv("SESSIONE_OPERATORE_ORE", "6")
    configurazione = Impostazioni(**valori)
    assert (
        configurazione.sessione_artigiano_giorni,
        configurazione.sessione_operatore_ore,
    ) == (9, 6)
    with pytest.raises(ValidationError):
        Impostazioni(**valori, sessione_operatore_ore=0)


def test_seed_aggiunge_due_account_collegati_e_non_li_sovrascrive(db):
    cli.esegui_seed(db, "PasswordDiProva!2026")
    artigiano = db.scalar(
        select(cli.Utente).where(cli.Utente.email == "artigiano@example.com")
    )
    bottega = profilo_di(db, artigiano.id)
    assert canali_collegati(db, bottega.id) == ["facebook", "instagram"]
    account = db.scalar(
        select(AccountSocial).where(
            AccountSocial.profilo_id == bottega.id,
            AccountSocial.piattaforma == "instagram",
        )
    )
    account.stato = "scollegato"
    account.id_pagina = "pagina-modificata"
    cli.esegui_seed(db, "PasswordDiversa!2026")
    assert (
        db.scalar(
            select(func.count())
            .select_from(AccountSocial)
            .where(AccountSocial.profilo_id == bottega.id)
        )
        == 2
    )
    assert account.stato == "scollegato"
    assert account.id_pagina == "pagina-modificata"


def test_cli_cambia_password_delega_e_non_stampa_la_password(db, monkeypatch, capsys):
    chiamate = []

    @contextmanager
    def transazione():
        yield db

    monkeypatch.setattr(cli, "transazione", transazione)
    monkeypatch.setattr(cli, "getpass", lambda _: "PasswordSoloTest!2026")
    monkeypatch.setattr(cli, "cambia_password", lambda *args: chiamate.append(args))
    assert cli.main(["cambia-password", "--email", "utente@example.test"]) == 0
    assert chiamate == [(db, "utente@example.test", "PasswordSoloTest!2026")]
    assert capsys.readouterr().out == "Password cambiata.\n"

    def errore(*args):
        raise NonTrovato("Utente non trovato.")

    monkeypatch.setattr(cli, "cambia_password", errore)
    assert cli.main(["cambia-password", "--email", "utente@example.test"]) == 1
    assert capsys.readouterr().err == "Utente non trovato.\n"


def test_fabbrica_campagna_con_piano_debole(db):
    record = campagna_con_piano_da_rivedere(db)
    assert record.stato == "piano_da_rivedere"
    assert len(campagne.foto_della_campagna(db, record.id)) == 4
    assert contenuti.piano_corrente(db, record.id).debole is True


def test_valori_di_dominio_nuovi_del_piano():
    assert set(artigiani_domain.STATI_ACCOUNT) == {"collegato", "scaduto", "scollegato"}
    assert set(campagne_domain.ORIGINI_GRUPPO) == {"caricate", "create_ai"}
    assert set(campagne_domain.ORIGINI_FOTO) == {"caricata", "creata_ai", "cartolina"}
    assert set(campagne_domain.TIPI_CONTENUTO) == {
        "pezzo_finito",
        "dettaglio",
        "lavorazione",
        "persona",
        "ambientato",
        "evento",
    }
    assert set(contenuti_domain.FORMATI_POST) == {"singola", "carosello"}
    assert set(contenuti_domain.TIPI_RIEMPITIVO) == {
        "archivio",
        "cartolina",
        "immagine_ai",
    }
    assert set(contenuti_domain.TIPI_INTERVENTO) == {
        "generazione",
        "rigenera_totale",
        "rigenera_da_proposta",
        "modifica_operatore",
        "ritocco_foto",
        "scelta_foto",
        "cambio_foto",
    }
    assert set(contenuti_domain.LIVELLI_VALIDATORE) == {"blocco", "avviso"}
    assert set(contenuti_domain.TIPI_ERRORE_GENERAZIONE) == {
        "temporaneo",
        "risposta",
        "configurazione",
        "richiesta",
        "rifiuto",
    }
    assert set(contenuti_domain.TIPI_INTERVENTO_IN_CORSO) == {
        "rigenera_totale",
        "rigenera_da_proposta",
        "ritocco_foto",
    }


def test_schede_canali_numeri_esatti_r21():
    assert contenuti_domain.SCHEDE_CANALE["facebook"] == {
        "max_caratteri": 500,
        "max_hashtag": 3,
        "limite_caratteri": 5000,
        "limite_hashtag": 30,
        "max_foto": 10,
    }
    assert contenuti_domain.SCHEDE_CANALE["instagram"] == {
        "max_caratteri": 600,
        "max_hashtag": 5,
        "limite_caratteri": 2200,
        "limite_hashtag": 30,
        "max_foto": 10,
    }


@pytest.mark.parametrize("stato", ["approvato", "fallito", "pubblicato", "annullato"])
def test_approva_rifiuta_stati_fuori_revisione_senza_mutazioni(db, stato):
    record = campagna_in_revisione(db)
    passato = post_da_approvare(
        db, campagna_id=record.id, data_ora=ORA - timedelta(days=1)
    )
    futuro = post_da_approvare(db, campagna_id=record.id)
    estraneo = post_da_approvare(db, campagna_id=record.id, stato=stato)
    with pytest.raises(StatoNonValido):
        contenuti.approva_post(db, record.id, ORA)
    db.expire_all()
    assert passato.stato == futuro.stato == "da_approvare"
    assert estraneo.stato == stato


def test_seed_completa_account_mancante_senza_duplicare(db):
    cli.esegui_seed(db, "PasswordDiProva!2026")
    record = db.scalar(
        select(AccountSocial).where(AccountSocial.piattaforma == "facebook")
    )
    db.delete(record)
    db.flush()
    cli.esegui_seed(db, "PasswordDiProva!2026")
    assert db.scalar(select(func.count()).select_from(AccountSocial)) == 2


def test_errori_di_configurazione_non_mostrano_segreti():
    segreto = "CredenzialeFintaDaNonMostrare!2026"
    with pytest.raises(ValidationError) as errore:
        Impostazioni(
            _env_file=None,
            database_url={"credenziale": segreto},
            database_url_test="postgresql://finto",
        )
    messaggio = str(errore.value)
    assert "database_url" in messaggio
    assert segreto not in messaggio
    assert "input_value" not in messaggio


def test_contratti_scrittura_non_fanno_commit(db, monkeypatch):
    def commit_vietato():
        raise AssertionError("I service e le fabbriche non fanno commit.")

    monkeypatch.setattr(db, "commit", commit_vietato)
    record = campagna_in_revisione(db)
    post_da_approvare(db, campagna_id=record.id)
    campagne.aggiungi_foto(db, record.id, "cartolina", "x.png", "image/png", 1080, 1080)
    campagne.registra_decisione(
        db, record, utente(db, "operatore").id, "nota", None, "Nota", []
    )
    contenuti.approva_post(db, record.id, ORA)
    campagne.cambia_stato(db, record, "attiva", ora=ORA)
    assert record.stato == "attiva"
