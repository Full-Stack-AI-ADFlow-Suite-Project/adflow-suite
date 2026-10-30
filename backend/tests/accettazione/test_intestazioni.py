"""Intestazioni di sicurezza delle risposte HTTP (T4-102, rischio R-01).

L'atteso viene da `accettazione-post-mvp.md` §5.4 e da OWASP ASVS V3
(intestazioni di sicurezza di base): CSP (almeno `frame-ancestors`), HSTS,
`X-Content-Type-Options: nosniff`, `Referrer-Policy`, `X-Frame-Options`.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.moduli.accesso.service import utente_corrente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza, foto, gruppo

INTESTAZIONI = (
    "content-security-policy",
    "strict-transport-security",
    "x-content-type-options",
    "referrer-policy",
    "x-frame-options",
)


@pytest.mark.xfail(
    strict=True,
    reason="RL-015 (R-01): l'app non imposta le intestazioni di sicurezza "
    "globali: nessuna CSP, nessun HSTS, nessun Referrer-Policy, nessun "
    "X-Frame-Options e X-Content-Type-Options manca su tutte le risposte "
    "che non sono file di foto",
)
def test_le_risposte_api_portano_le_intestazioni_di_sicurezza(client: TestClient):
    """Cinque intestazioni attese su ogni risposta dell'API (T4-102)."""
    mancanti = {}
    for percorso in ("/api/health", "/api/consorzio", "/api/campagne"):
        risposta = client.get(percorso)
        assenti = [h for h in INTESTAZIONI if not risposta.headers.get(h)]
        if assenti:
            mancanti[f"{percorso} ({risposta.status_code})"] = assenti
    assert not mancanti, f"intestazioni di sicurezza assenti: {mancanti}"


def test_le_risposte_di_errore_hanno_id_e_niente_cache(client: TestClient):
    """Ciò che c'è già: X-Request-ID generato dal server e no-store dove serve."""
    risposta = client.get("/api/health")
    assert risposta.headers.get("x-request-id")
    protetta = client.get("/api/campagne")
    assert protetta.status_code == 401
    assert protetta.headers.get("cache-control") == "no-store"


def test_i_file_delle_foto_portano_nosniff(
    db: Session, client: TestClient, tmp_path, utente_di_prova
):
    """L'unica difesa presente oggi: nosniff sui file delle foto (R-01)."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        artigiano = utente_di_prova("artigiano")
        bottega = profilo(db, utente_id=artigiano.id)
        campagna = campagna_in_bozza(db, profilo_id=bottega.id)
        mazzo = gruppo(db, campagna)
        buffer = io.BytesIO()
        Image.new("RGB", (1080, 1350), (80, 80, 80)).save(buffer, format="JPEG")
        nome_file = archivio.salva(buffer.getvalue(), "jpg")
        immagine = foto(db, gruppo=mazzo, file=nome_file)
        db.flush()

        risposta = client.get(f"/api/foto/{immagine.id}/file")
        assert risposta.status_code == 200
        assert risposta.headers["x-content-type-options"] == "nosniff"
        assert risposta.headers["content-type"] == "image/jpeg"
