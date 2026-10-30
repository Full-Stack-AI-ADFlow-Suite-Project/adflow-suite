"""Test del perimetro MVP (ADR-114, `perimetro-mvp.md`).

Raccoglie i controlli sulle funzioni tolte o sostituite nell'MVP:
- `POST /campagne/{id}/prosegui` tolto (A3);
- il logo del profilo non esiste più (A7);
- la stella (`da_usare`) sulle foto non esiste più nelle API, nella generazione
  e nelle regole del piano (A11);
- `archivio` e `cartolina` non sono più riempitivi del piano (A6, A10).
"""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.adapters.ai import AIFinto, usa_ai
from app.adapters.archivio import ArchivioDisco, ArchivioFinto, usa_archivio
from app.moduli.campagne import service as campagne
from app.moduli.campagne.models import Foto, GruppoFoto
from app.moduli.contenuti import domain, piano
from app.moduli.contenuti.service import post_della_campagna
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_con_piano_da_rivedere,
    campagna_in_bozza,
)
from tests.moduli.contenuti.test_generazione import (
    _campagna,
    _foto_del_post,
    _foto_ids,
    _job,
    transazioni_di_prova,
)
from tests.moduli.contenuti.test_piano import (
    FINE,
    INIZIO,
    _controlla,
    _foto,
    _gruppo,
    _limiti,
    _piano_valido,
    _regole,
    limiti_per_canale,
)

__all__ = ["transazioni_di_prova"]


def _crea_png(larghezza: int, altezza: int) -> bytes:
    buf = BytesIO()
    Image.new("RGB", (larghezza, altezza), (120, 80, 60)).save(buf, format="PNG")
    return buf.getvalue()


def test_prosegui_non_esiste_piu(db, client, utente_di_prova):
    """ADR-114, A3: l'endpoint è tolto e una campagna vecchia resta ferma."""
    campagna = campagna_con_piano_da_rivedere(db)
    utente_di_prova("operatore")

    assert client.post(f"/api/campagne/{campagna.id}/prosegui").status_code == 404

    db.refresh(campagna)
    assert campagna.stato == "piano_da_rivedere"


def test_il_logo_non_esiste_piu(db, client, utente_di_prova):
    """ADR-114, A7: le rotte `/profilo/logo` non esistono e il profilo non espone `logo`."""
    art = utente_di_prova("artigiano")
    profilo(db, utente_id=art.id)

    risposta = client.get("/api/profilo")
    assert risposta.status_code == 200
    assert "logo" not in risposta.json()

    for metodo in ("get", "put", "delete"):
        assert getattr(client, metodo)("/api/profilo/logo").status_code == 404


def test_la_stella_non_esiste_piu(
    client: TestClient, utente_di_prova, db: Session, tmp_path: Path
):
    """ADR-114, A11: `PUT /foto/{id}` è tolto e le risposte non portano `da_usare`."""
    with usa_archivio(ArchivioDisco(tmp_path)):
        art = utente_di_prova("artigiano")
        prof = profilo(db, utente_id=art.id)
        camp = campagna_in_bozza(db, profilo_id=prof.id)
        gruppo = GruppoFoto(
            profilo_id=camp.profilo_id,
            campagna_id=camp.id,
            origine="caricate",
        )
        db.add(gruppo)
        db.flush()

        res = client.post(
            f"/api/campagne/{camp.id}/foto",
            data={"gruppo_id": str(gruppo.id)},
            files={"file": ("foto.png", BytesIO(_crea_png(1080, 1080)), "image/png")},
        )
        assert res.status_code == 201
        foto_id = res.json()["id"]
        assert "da_usare" not in res.json()

        res_put = client.put(f"/api/foto/{foto_id}", json={"da_usare": True})
        assert res_put.status_code == 405

        db.expire_all()
        assert db.get(Foto, foto_id).da_usare is False
        dettaglio = client.get(f"/api/campagne/{camp.id}").json()
        assert all("da_usare" not in f for g in dettaglio["gruppi"] for f in g["foto"])


def test_una_stella_gia_salvata_non_conta_piu(db):
    """ADR-114, A11: 8 foto e 6 post, l'ultima ha `da_usare` e resta un doppione.

    La colonna resta nel database, ma la generazione non la legge: la foto non
    entra nel piano per forza e l'analisi dell'AI resta com'è.
    """
    with usa_archivio(ArchivioFinto()), usa_ai(AIFinto()) as ai:
        campagna = _campagna(db, n_foto=8)
        ids = _foto_ids(db, campagna)
        con_stella, altra = ids[7], ids[0]
        campagne.foto_per_id(db, [con_stella])[0].da_usare = True
        db.commit()
        ai.comanda_analisi(con_stella, simile_a=altra)

        _job(campagna.id)

        assert campagna.stato == "in_revisione"
        immagini = {f.id: f for f in campagne.foto_della_campagna(db, campagna.id)}
        assert immagini[con_stella].analisi_ai["simile_a"] == altra
        assert immagini[altra].analisi_ai["simile_a"] is None
        usate = {
            f for p in post_della_campagna(db, campagna.id) for f in _foto_del_post(p)
        }
        assert con_stella not in usate


def test_una_stella_gia_salvata_non_e_piu_una_regola():
    """ADR-114, A11: `foto.da_usare` resta nel database, il controllo non lo legge."""
    con_stella = _foto(8)
    con_stella.da_usare = True
    gruppi = [_gruppo(1, [_foto(n) for n in range(1, 8)] + [con_stella])]
    limiti = limiti_per_canale(["facebook", "instagram"], 3, INIZIO, FINE, gruppi)
    contenuto = _piano_valido(limiti)

    assert _controlla(contenuto, limiti, gruppi) == []
    assert "foto_con_stella" not in piano.REGOLE


@pytest.mark.parametrize("riempitivo", ["archivio", "cartolina"])
def test_archivio_e_cartolina_non_sono_riempitivi_del_piano(riempitivo):
    """ADR-114: restano valori ammessi nel database, il piano non li chiede."""
    assert piano.RIEMPITIVI_DEL_PIANO == ("immagine_ai",)
    assert riempitivo in domain.TIPI_RIEMPITIVO
    limiti, gruppi = _limiti(5, canali=("instagram",))
    contenuto = _piano_valido(limiti)
    contenuto["uscite"][5]["post"][0]["riempitivo"] = riempitivo

    assert set(_regole(_controlla(contenuto, limiti, gruppi))) == {"piano_malformato"}
