"""T1-04: valori ammessi e letture comuni del modulo artigiani."""
from app.moduli.artigiani import domain, service
from app.moduli.artigiani.models import ProfiloBottega
from app.moduli.artigiani.service import profilo_di
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo


def test_profilo_di_restituisce_il_profilo_dell_utente(db):
    atteso = profilo(db)
    profilo(db)
    assert profilo_di(db, atteso.utente_id) is atteso


def test_profilo_di_senza_profilo_restituisce_none(db):
    assert profilo_di(db, utente(db).id) is None


def test_frequenza_in_post_a_settimana():
    assert domain.POST_A_SETTIMANA == {
        "f1_2": 2,
        "f3_4": 3,
        "f5_piu": 5,
        "decidete_voi": 3,
    }


def test_valori_ammessi_di_plan_2():
    assert set(domain.CANALI) == {"facebook", "instagram"}
    assert set(domain.OBIETTIVI) == {"vendere", "negozio", "notorieta", "fidelizzare"}
    assert set(domain.CORTESIE) == {"tu", "lei", "dipende"}
    assert set(domain.FASCE_PREZZO) == {"accessibile", "media", "alta"}
    assert len(domain.TIPI_PRODOTTO) == 6
    assert len(domain.VALORI) == 6
    assert len(domain.TONI) == 5
    assert len(domain.TIPI_EVENTO) == 6


def test_gli_obbligatori_sono_colonne_non_nulle():
    colonne = ProfiloBottega.__table__.columns
    assert all(not colonne[nome].nullable for nome in domain.OBBLIGATORI)


def test_la_fabbrica_usa_valori_ammessi(db):
    bottega = profilo(db)
    assert bottega.tipo_prodotto in domain.TIPI_PRODOTTO
    assert bottega.obiettivo in domain.OBIETTIVI
    assert set(bottega.canali) <= set(domain.CANALI)
    assert bottega.frequenza in domain.FREQUENZE


def test_profilo_per_id_restituisce_il_profilo_o_none(db):
    atteso = profilo(db)
    profilo(db)
    assert service.profilo(db, atteso.id) is atteso
    assert service.profilo(db, atteso.id + 1000) is None


def test_post_a_settimana_di_ogni_frequenza():
    for frequenza, numero in domain.POST_A_SETTIMANA.items():
        assert service.post_a_settimana(frequenza) == numero


def test_post_a_settimana_senza_frequenza_vale_decidete_voi():
    atteso = domain.POST_A_SETTIMANA["decidete_voi"]
    assert service.post_a_settimana(None) == atteso
    assert service.post_a_settimana("") == atteso
    assert service.post_a_settimana("inesistente") == atteso
