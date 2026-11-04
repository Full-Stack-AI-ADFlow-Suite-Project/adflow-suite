"""Input estremi che producono 500 (T4-104, trovato con schemathesis).

§6 della simulazione: «ogni 500 e ogni risposta fuori schema» è un rilievo.
Tre classi, tutte deterministiche, riprodotte con `uvx schemathesis run` e a
mano:

1. id numerici oltre il range di PostgreSQL (`int4`, 2 147 483 647): FastAPI
   accetta qualsiasi intero di Python e il database va in `InternalError` → 500;
2. `GET /api/storico-ai?tipo=<valore non ammesso>`: il filtro finisce in una
   query su una colonna enum e il database rifiuta il valore → 500;
3. `GET /api/archivio` per un artigiano senza profilo (rotta congelata):
   invece del 404 documentato arriva un 500.

Il 500 è la risposta sbagliata: l'atteso è 404 (id che non esiste) o 422
(valore non ammesso). RL-026 è corretto.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.moduli.artigiani.fabbrica import profilo

ID_OLTRE_IL_LIMITE = 9_999_999_999_999


def test_un_id_di_percorso_enorme_non_fa_500(client: TestClient, db, utente_di_prova):
    artigiano = utente_di_prova("artigiano")
    profilo(db, utente_id=artigiano.id)
    risposta = client.get(f"/api/foto/{ID_OLTRE_IL_LIMITE}/file")
    assert risposta.status_code in (404, 422), f"risposta {risposta.status_code}"


def test_un_tipo_di_chiamata_non_ammesso_non_fa_500(
    client: TestClient, utente_di_prova
):
    utente_di_prova("operatore")
    risposta = client.get("/api/storico-ai?tipo=spazzatura")
    assert risposta.status_code == 422, f"risposta {risposta.status_code}"
