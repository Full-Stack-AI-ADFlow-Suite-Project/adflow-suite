"""Disco pieno durante un upload (T4-105, §7.4).

Atteso: errore chiaro, nessun file a metà, originale intatto.
"""

from __future__ import annotations

import errno
import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.moduli.campagne.models import Foto
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza, gruppo


def test_disco_pieno_durante_un_upload(
    db: Session, client: TestClient, utente_di_prova, tmp_path, monkeypatch
):
    """ENOSPC al salvataggio: errore chiaro e nessuna foto a metà."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        artigiano = utente_di_prova("artigiano")
        bottega = profilo(db, utente_id=artigiano.id)
        campagna = campagna_in_bozza(db, profilo_id=bottega.id)
        mazzo = gruppo(db, campagna)
        db.flush()
        prima = db.scalar(select(func.count()).select_from(Foto))

        def disco_pieno(*_argomenti, **_campi):
            raise OSError(errno.ENOSPC, "No space left on device")

        monkeypatch.setattr(ArchivioDisco, "salva", disco_pieno)
        buffer = io.BytesIO()
        Image.new("RGB", (1080, 1350), (70, 70, 70)).save(buffer, format="JPEG")
        risposta = client.post(
            f"/api/campagne/{campagna.id}/foto",
            files={"file": ("foto.jpg", buffer.getvalue(), "image/jpeg")},
            data={"gruppo_id": str(mazzo.id)},
        )

    assert risposta.status_code in (
        413,
        503,
    ), f"errore non chiaro: {risposta.status_code} {risposta.text[:80]}"
    dopo = db.scalar(select(func.count()).select_from(Foto))
    assert dopo == prima, "è rimasta una foto a metà nel database"
