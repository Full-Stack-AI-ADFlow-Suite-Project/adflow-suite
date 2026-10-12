import pytest

from app.core.errori import NonTrovato
from app.moduli.accesso import service
from tests.moduli.accesso.fabbrica import utente


@pytest.mark.parametrize("attivo", [True, False])
def test_utente_legge_anche_il_destinatario_non_attivo(db, attivo):
    persona = utente(db, attivo=attivo)
    assert service.utente(db, persona.id) is persona
    assert persona.attivo is attivo


def test_utente_assente(db):
    with pytest.raises(NonTrovato, match="Utente non trovato"):
        service.utente(db, -1)


def test_operatori_attivi_include_admin_esclude_artigiani_e_non_attivi(db):
    operatore = utente(db, "operatore")
    admin = utente(db, "admin")
    utente(db, "artigiano")
    utente(db, "operatore", attivo=False)
    utente(db, "admin", attivo=False)
    assert [p.id for p in service.operatori(db)] == [operatore.id, admin.id]


def test_operatori_elenco_vuoto(db):
    utente(db, "artigiano")
    assert service.operatori(db) == []
