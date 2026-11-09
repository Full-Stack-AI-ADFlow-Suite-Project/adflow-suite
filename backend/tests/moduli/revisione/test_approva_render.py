"""All'approvazione si rendono le foto dei post approvati (RT-07, ADR-124)."""

from datetime import datetime, timedelta, timezone


from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.moduli.campagne.models import Foto
from app.moduli.revisione import service as revisione
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare

from tests.moduli.pubblicazione.test_render_approvato import _jpeg


def test_approva_fissa_il_render_dei_post_approvati(db):
    adesso = datetime.now(timezone.utc)
    campagna = campagna_in_revisione(db)
    post = post_da_approvare(
        db, campagna_id=campagna.id, data_ora=adesso + timedelta(days=10)
    )
    with usa_archivio(ArchivioFinto()) as archivio:
        legame = post.versione_corrente.legami_foto[0]
        db.get(Foto, legame.foto_id).file = archivio.salva(_jpeg(), "jpg")
        db.flush()
        operatore = utente(db, ruolo="operatore")

        revisione.approva(db, campagna.id, operatore, adesso)

        assert post.stato == "approvato"
        assert legame.render is not None
        assert archivio.esiste_derivato(legame.foto_id, legame.render)
