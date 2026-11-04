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

import io

from fastapi.testclient import TestClient
from PIL import Image

from app.adapters.archivio import ArchivioDisco, usa_archivio
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_in_bozza,
    campagna_in_revisione,
    gruppo,
)

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


def test_un_artigiano_enorme_nel_filtro_non_fa_500(client: TestClient, utente_di_prova):
    utente_di_prova("operatore")
    risposta = client.get(f"/api/campagne?artigiano={ID_OLTRE_IL_LIMITE}")
    assert risposta.status_code == 422, f"risposta {risposta.status_code}"


def test_una_campagna_enorme_nel_filtro_dello_storico_non_fa_500(
    client: TestClient, utente_di_prova
):
    utente_di_prova("operatore")
    for percorso in ("/api/storico-ai", "/api/storico-ai/numeri"):
        risposta = client.get(f"{percorso}?campagna_id={ID_OLTRE_IL_LIMITE}")
        assert (
            risposta.status_code == 422
        ), f"{percorso}: risposta {risposta.status_code}"


def test_un_gruppo_enorme_nell_upload_non_fa_500(
    client: TestClient, db, utente_di_prova, tmp_path
):
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        artigiano = utente_di_prova("artigiano")
        bottega = profilo(db, utente_id=artigiano.id)
        campagna = campagna_in_bozza(db, profilo_id=bottega.id)
        gruppo(db, campagna)
        db.flush()
        buffer = io.BytesIO()
        Image.new("RGB", (1080, 1350), (70, 70, 70)).save(buffer, format="JPEG")
        risposta = client.post(
            f"/api/campagne/{campagna.id}/foto",
            files={"file": ("foto.jpg", buffer.getvalue(), "image/jpeg")},
            data={"gruppo_id": str(ID_OLTRE_IL_LIMITE)},
        )
    assert risposta.status_code == 422, f"risposta {risposta.status_code}"


def test_una_foto_enorme_nella_richiesta_non_fa_500(
    client: TestClient, db, utente_di_prova
):
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    db.flush()
    utente_di_prova("operatore")
    risposta = client.post(
        f"/api/campagne/{campagna.id}/richiesta",
        json={"domanda": "x", "foto": [ID_OLTRE_IL_LIMITE]},
    )
    assert risposta.status_code == 422, f"risposta {risposta.status_code}"
