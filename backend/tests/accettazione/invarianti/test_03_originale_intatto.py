"""§1.3 — La foto originale non si modifica e non si perde mai.

Attacchi di §4.3: dopo sistemazione, ritaglio, pubblicazione e cambio foto
l'hash del file originale resta identico.
"""

from __future__ import annotations

import hashlib
import io
from datetime import datetime, timedelta, timezone

from PIL import Image
from sqlalchemy import select

from app.adapters.archivio import ArchivioDisco, usa_archivio
from app.adapters.social import SocialFinto, usa_social
from app.moduli.campagne import service as campagne_service
from app.moduli.campagne.models import Foto
from app.moduli.pubblicazione import service as pubblicazione
from app.moduli.revisione import interventi
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva
from tests.moduli.contenuti.fabbrica import post_approvato


def _sha(dati: bytes) -> str:
    return hashlib.sha256(dati).hexdigest()


def test_l_originale_resta_identico_attraverso_tutte_le_lavorazioni(
    db, utente_di_prova, tmp_path
):
    """Hash uguale prima e dopo sistemazione, cambio foto e pubblicazione (§1.3)."""
    archivio = ArchivioDisco(tmp_path)
    with usa_archivio(archivio):
        artigiano = utente_di_prova("artigiano")
        bottega = profilo(db, utente_id=artigiano.id)
        adesso = datetime.now(timezone.utc)
        campagna = campagna_attiva(
            db,
            profilo_id=bottega.id,
            inizio=adesso.date() - timedelta(days=1),
            fine=adesso.date() + timedelta(days=30),
        )
        post = post_approvato(
            db,
            campagna_id=campagna.id,
            data_ora=adesso + timedelta(minutes=30),  # ancora fuori dal margine
        )
        # una foto libera della stessa campagna, con un file vero su disco
        libera = db.scalars(
            select(Foto)
            .where(Foto.campagna_id == campagna.id, Foto.n_utilizzi == 0)
            .order_by(Foto.id)
        ).first()
        buffer = io.BytesIO()
        Image.new("RGB", (3000, 2000), (120, 30, 60)).save(buffer, format="JPEG")
        originale = buffer.getvalue()
        libera.file = archivio.salva(originale, "jpg")
        db.flush()
        atteso = _sha(originale)

        campagne_service.foto_sistemata(db, libera.id, canale="instagram")
        assert (
            _sha(archivio.leggi(libera.file)) == atteso
        ), "la sistemazione ha toccato l'originale"

        interventi.cambia_foto(db, post.id, libera.id, artigiano, adesso)
        assert (
            _sha(archivio.leggi(libera.file)) == atteso
        ), "il cambio foto ha toccato l'originale"

        # il tempo passa: il post diventa dovuto e il tick lo pubblica
        post.data_ora = adesso - timedelta(minutes=1)
        db.flush()
        social = SocialFinto()
        with usa_social(social):
            pubblicazione.pubblica_dovuti(db, adesso)
        assert len(social.pubblicazioni) == 1
        assert (
            _sha(archivio.leggi(libera.file)) == atteso
        ), "la pubblicazione ha toccato l'originale"
