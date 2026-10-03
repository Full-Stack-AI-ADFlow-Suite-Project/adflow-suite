"""richiede_ruolo(): controllo del ruolo sopra utente_corrente."""
import pytest

from app.core.errori import NonPermesso
from app.moduli.accesso.service import richiede_ruolo
from tests.moduli.accesso.fabbrica import utente


def test_richiede_ruolo_ammette_il_ruolo_previsto(db):
    operatore = utente(db, "operatore")
    assert richiede_ruolo("operatore", "admin")(operatore) is operatore


def test_richiede_ruolo_rifiuta_un_altro_ruolo(db):
    artigiano = utente(db, "artigiano")
    with pytest.raises(NonPermesso):
        richiede_ruolo("operatore")(artigiano)


def test_richiede_ruolo_si_costruisce_senza_sessione():
    # I router la chiamano all'import: non deve sollevare nulla.
    assert callable(richiede_ruolo("operatore"))
