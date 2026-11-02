"""Attacchi all'indirizzo pubblico delle foto (T4-102, §5.4 punto 5).

Firma scaduta, alterata, presa da un'altra foto, tagliata, con l'id cambiato o
inesistente: sempre 404, senza distinguere i motivi (enumerazione resistente).
La firma valida resta l'unico modo per leggere la foto.
"""

from __future__ import annotations

import io
import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.moduli.campagne import foto_pubblica, service
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza, foto, gruppo


@pytest.fixture
def due_foto(db: Session, client: TestClient, tmp_path):
    """Due foto con file vero su disco: una di A e una di B."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        bottega_a = profilo(db)
        bottega_b = profilo(db)
        campagna_a = campagna_in_bozza(db, profilo_id=bottega_a.id)
        campagna_b = campagna_in_bozza(db, profilo_id=bottega_b.id)
        buffer = io.BytesIO()
        Image.new("RGB", (1080, 1350), (60, 60, 90)).save(buffer, format="JPEG")
        nome_file = archivio.salva(buffer.getvalue(), "jpg")
        foto_a = foto(db, gruppo=gruppo(db, campagna_a), file=nome_file)
        foto_b = foto(db, gruppo=gruppo(db, campagna_b), file=nome_file)
        db.flush()
        yield {"a": foto_a.id, "b": foto_b.id}


def _url(foto_id: int, firma: str, canale: str = "instagram") -> str:
    return f"/api/foto/{foto_id}/pubblica?canale={canale}&firma={firma}"


def test_la_firma_valida_apre_la_foto(due_foto, client):
    """Il caso buono, per confronto: la firma valida dà 200."""
    scadenza = int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
    firma = foto_pubblica.componi_firma(due_foto["a"], "instagram", scadenza)
    risposta = client.get(_url(due_foto["a"], firma))
    assert risposta.status_code == 200
    assert risposta.headers["content-type"] == "image/jpeg"


def test_la_firma_scaduta_dà_404(due_foto, client):
    scadenza = int((datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp())
    firma = foto_pubblica.componi_firma(due_foto["a"], "instagram", scadenza)
    assert client.get(_url(due_foto["a"], firma)).status_code == 404


def test_la_firma_alterata_dà_404(due_foto, client):
    scadenza = int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
    firma = foto_pubblica.componi_firma(due_foto["a"], "instagram", scadenza)
    alterata = firma[:-2] + ("00" if not firma.endswith("00") else "11")
    assert client.get(_url(due_foto["a"], alterata)).status_code == 404


def test_la_firma_di_un_altra_foto_dà_404(due_foto, client):
    """La firma di B usata per la foto di A non vale (R-13: firma per foto)."""
    scadenza = int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
    firma_di_b = foto_pubblica.componi_firma(due_foto["b"], "instagram", scadenza)
    assert client.get(_url(due_foto["a"], firma_di_b)).status_code == 404
    # e l'id cambiato con la firma di A non vale per B
    firma_di_a = foto_pubblica.componi_firma(due_foto["a"], "instagram", scadenza)
    assert client.get(_url(due_foto["b"], firma_di_a)).status_code == 404


def test_la_firma_tagliata_o_vuota_dà_404(due_foto, client):
    scadenza = int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
    firma = foto_pubblica.componi_firma(due_foto["a"], "instagram", scadenza)
    assert client.get(_url(due_foto["a"], firma[: len(firma) // 2])).status_code == 404
    assert client.get(_url(due_foto["a"], "")).status_code == 404
    assert client.get(_url(due_foto["a"], "_")).status_code == 404


def test_id_inesistente_o_canale_sconosciuto_dà_404(due_foto, client):
    scadenza = int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
    firma = foto_pubblica.componi_firma(999_999, "instagram", scadenza)
    assert client.get(_url(999_999, firma)).status_code == 404
    firma_tiktok = foto_pubblica.componi_firma(due_foto["a"], "tiktok", scadenza)
    assert (
        client.get(_url(due_foto["a"], firma_tiktok, canale="tiktok")).status_code
        == 404
    )


def test_i_tempi_dei_404_non_si_distinguono(due_foto, client):
    """Tutte le varianti rifiutate rispondono 404: i tempi non rivelano quale
    controllo ha fermato la richiesta (i numeri finiscono nel report T4-102)."""
    scadenza = int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
    firma_valida = foto_pubblica.componi_firma(due_foto["a"], "instagram", scadenza)
    casi = {
        "valida": _url(due_foto["a"], firma_valida),
        "alterata": _url(due_foto["a"], firma_valida[:-2] + "zz"),
        "altra_foto": _url(due_foto["b"], firma_valida),
        "inesistente": _url(999_999, firma_valida),
    }
    tempi: dict[str, list[float]] = {nome: [] for nome in casi}
    codici: dict[str, set[int]] = {nome: set() for nome in casi}
    for _ in range(10):
        for nome, url in casi.items():
            inizio = time.perf_counter()
            risposta = client.get(url)
            tempi[nome].append((time.perf_counter() - inizio) * 1000)
            codici[nome].add(risposta.status_code)
    for nome, codici_caso in codici.items():
        assert codici_caso == {200 if nome == "valida" else 404}, nome
    medie = {nome: sum(v) / len(v) for nome, v in tempi.items()}
    rifiutate = [medie[n] for n in medie if n != "valida"]
    # soft: i 404 devono restare dello stesso ordine tra loro (nessuno 10 volte
    # più lento degli altri rivelerebbe quale controllo ha fermato la richiesta)
    assert max(rifiutate) < 10 * (min(rifiutate) + 1), medie
