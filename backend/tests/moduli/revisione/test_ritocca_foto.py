"""L'intervento `ritocca_foto` (RT-28, ADR-124): variante della foto e privacy, senza AI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.moduli.campagne import service as campagne
from app.moduli.campagne import varianti as var
from app.moduli.campagne.diagnosi import diagnosi
from app.moduli.contenuti import service as contenuti
from app.moduli.contenuti.models import Post, VersionePost, VersionePostFoto
from app.moduli.revisione.models import Approvazione
from tests import immagini
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_approvato, post_da_approvare

ZONE = [{"id": "z1", "origine": "ai", "ruolo": "targa", "b": [10, 10, 40, 40]}]


@pytest.fixture
def archivio():
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


def _prepara_foto(db, archivio, foto, *, varianti_salvate=True, zone=()):
    scura = immagini.gradiente((1600, 1200), (4, 4, 6), (70, 60, 55), verticale=True)
    foto.file = archivio.salva(immagini.jpeg_qualita(scura, 92), "jpg")
    if varianti_salvate:
        locale = {
            "misure": {"angolo_linee": None, "caduta_bordi": 0.0},
            "fasce": {"esposizione": "scura"},
            "exif": {},
            "candidati": {"volti": [], "quadrilateri": []},
        }
        ai = {"note": ["scura"], "centro": None, "zone": [], "piana": None, "volti": []}
        ritocco = var.ritocco_di_foto(foto, diagnosi(ai, locale), locale)
        ritocco["privacy"] = list(zone)
        foto.analisi_ai = {"soggetto_box": None, "ritocco": ritocco}
    db.flush()


def _due_post_stessa_foto(db, archivio, campagna, **opzioni):
    uno = post_da_approvare(db, campagna_id=campagna.id, canale="instagram")
    due = post_da_approvare(db, campagna_id=campagna.id, canale="facebook")
    legame_uno = uno.versione_corrente.legami_foto[0]
    legame_due = due.versione_corrente.legami_foto[0]
    legame_due.foto_id = legame_uno.foto_id
    db.flush()
    _prepara_foto(
        db, archivio, campagne.foto_per_id(db, [legame_uno.foto_id])[0], **opzioni
    )
    db.expire_all()
    return uno, due


def _ritocca(client, post, **corpo):
    return client.post(f"/api/post/{post.id}/ritocca-foto", json=corpo)


def _versioni(db, post) -> list[VersionePost]:
    db.expire_all()
    return list(
        db.scalars(
            select(VersionePost)
            .where(VersionePost.post_id == post.id)
            .order_by(VersionePost.numero)
        )
    )


# --- In revisione ------------------------------------------------------------------


def test_la_scelta_nasce_come_versione_ritocco_foto_per_tutti_i_post_con_la_stessa_foto(
    db, client, utente_di_prova, archivio
):
    operatore = utente_di_prova("operatore")
    uno, due = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))

    risposta = _ritocca(client, uno, variante="spinta")

    assert risposta.status_code == 200
    assert risposta.json() == {
        "stato": "ok",
        "post_aggiornati": [uno.id, due.id],
        "post_non_aggiornati": [],
    }
    for post in (uno, due):
        prima, dopo = _versioni(db, post)
        assert (dopo.numero, dopo.tipo_intervento, dopo.autore_id) == (
            2,
            "ritocco_foto",
            operatore.id,
        )
        assert (dopo.testo, dopo.hashtag) == (prima.testo, prima.hashtag)
        legame = dopo.legami_foto[0]
        assert legame.foto_id == prima.legami_foto[0].foto_id
        assert legame.ritocco == {"variante": "spinta"}
        assert (
            legame.render is None
        )  # non è approvato: il render si fa all'approvazione


def test_il_validatore_dei_testi_non_cambia_esito(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    _versioni(db, uno)[0].errori_validazione = [
        {"regola": "R-09", "livello": "avviso", "messaggio": "x"}
    ]
    db.flush()
    assert _ritocca(client, uno, variante="spinta").status_code == 200
    prima, dopo = _versioni(db, uno)
    assert dopo.errori_validazione == prima.errori_validazione


def test_la_spunta_cade(db, client, utente_di_prova, archivio):
    operatore = utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    uno.controllato_da, uno.controllato_il = operatore.id, datetime.now(timezone.utc)
    db.flush()
    _ritocca(client, uno, variante="originale")
    db.refresh(uno)
    assert uno.controllato_da is None and uno.controllato_il is None


def test_non_conta_cicli_di_rigenerazione(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    _ritocca(client, uno, variante="originale")
    db.refresh(uno)
    assert uno.n_rigenerazioni_testo == 0


def test_cambiare_solo_la_privacy_tiene_la_variante_di_prima(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db), zone=ZONE)
    assert _ritocca(client, uno, variante="originale").status_code == 200
    assert _ritocca(client, uno, privacy=True).status_code == 200
    assert _versioni(db, uno)[-1].legami_foto[0].ritocco == {
        "variante": "originale",
        "privacy": True,
    }


def test_la_stessa_scelta_di_adesso_e_409(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    risposta = _ritocca(client, uno, variante="standard")  # la scelta di partenza
    assert risposta.status_code == 409
    assert len(_versioni(db, uno)) == 1


def test_un_secondo_post_gia_a_posto_non_riceve_una_versione_inutile(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, due = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    _ritocca(client, uno, variante="spinta")
    risposta = _ritocca(
        client, due, variante="originale"
    )  # per tutti e due: già Spinta
    assert risposta.status_code == 200
    assert len(_versioni(db, uno)) == 3 and len(_versioni(db, due)) == 3


def test_senza_niente_da_cambiare_422(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    assert _ritocca(client, uno).status_code == 422


@pytest.mark.parametrize(
    "corpo",
    [
        {"variante": "ottima"},
        {"variante": 3},
        {"privacy": "si"},
        {"variante": "spinta", "altro": 1},
    ],
)
def test_corpo_non_valido_422(db, client, utente_di_prova, archivio, corpo):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    assert _ritocca(client, uno, **corpo).status_code == 422


def test_una_variante_spenta_non_si_sceglie(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    # senza varianti salvate la Spinta è spenta (D6)
    uno, _ = _due_post_stessa_foto(
        db, archivio, campagna_in_revisione(db), varianti_salvate=False
    )
    assert _ritocca(client, uno, variante="spinta").status_code == 422
    assert _ritocca(client, uno, variante="originale").status_code == 200


def test_oscurare_senza_zone_422(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    assert _ritocca(client, uno, privacy=True).status_code == 422


def test_post_inesistente_404(client, utente_di_prova):
    utente_di_prova("operatore")
    assert (
        client.post(
            "/api/post/999999/ritocca-foto", json={"variante": "spinta"}
        ).status_code
        == 404
    )


# --- Stati ammessi e vietati -------------------------------------------------------


@pytest.mark.parametrize(
    "campi",
    [
        {"stato": "scartato"},
        {"stato": "annullato"},
        {"stato": "scaduto"},
        {"riempitivo": "immagine_ai"},
        {"riempitivo": "cartolina"},
    ],
)
def test_stati_vietati_409(db, client, utente_di_prova, archivio, campi):
    utente_di_prova("operatore")
    uno = post_da_approvare(db, campagna_id=campagna_in_revisione(db).id, **campi)
    _prepara_foto(
        db,
        archivio,
        campagne.foto_per_id(db, [uno.versione_corrente.legami_foto[0].foto_id])[0],
    )
    assert _ritocca(client, uno, variante="originale").status_code == 409


def test_con_un_intervento_in_corso_409(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    uno.intervento_in_corso, uno.intervento_dal = "rigenera_totale", datetime.now(
        timezone.utc
    )
    db.flush()
    assert _ritocca(client, uno, variante="spinta").status_code == 409


def test_i_post_dove_non_si_puo_la_risposta_lo_dice(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, due = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    due.intervento_in_corso, due.intervento_dal = "rigenera_totale", datetime.now(
        timezone.utc
    )
    db.flush()

    risposta = _ritocca(client, uno, variante="spinta").json()

    assert risposta["post_aggiornati"] == [uno.id]
    assert [p["post_id"] for p in risposta["post_non_aggiornati"]] == [due.id]
    assert "intervento in corso" in risposta["post_non_aggiornati"][0]["motivo"]
    assert len(_versioni(db, due)) == 1


def test_un_post_chiuso_con_la_stessa_foto_si_salta_in_silenzio(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, due = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    due.stato = "scartato"
    db.flush()
    risposta = _ritocca(client, uno, variante="spinta").json()
    assert (
        risposta["post_aggiornati"] == [uno.id]
        and risposta["post_non_aggiornati"] == []
    )


def test_la_vista_della_campagna_elenca_l_intervento(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    uno, due = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    dati = client.get(f"/api/campagne/{uno.campagna_id}/post").json()
    interventi = {
        p["post_id"]: p["interventi"] for u in dati["uscite"] for p in u["post"]
    }
    assert "ritocca_foto" in interventi[uno.id] and "ritocca_foto" in interventi[due.id]
    foto = next(
        p["foto"] for u in dati["uscite"] for p in u["post"] if p["post_id"] == uno.id
    )
    assert foto["varianti"]["disponibili"] == ["originale", "standard", "spinta"]
    _ritocca(client, uno, variante="spinta")
    dati = client.get(f"/api/campagne/{uno.campagna_id}/post").json()
    foto = next(
        p["foto"] for u in dati["uscite"] for p in u["post"] if p["post_id"] == uno.id
    )
    assert foto["varianti"]["scelta"] == "spinta"


# --- Permessi ----------------------------------------------------------------------


def test_l_artigiano_non_puo_ritoccare(db, client, utente_di_prova, archivio):
    utente_di_prova("artigiano")
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    assert _ritocca(client, uno, variante="spinta").status_code == 403


def test_senza_sessione_401(db, client, archivio):
    from app.main import app
    from app.moduli.accesso.service import utente_corrente

    app.dependency_overrides.pop(utente_corrente, None)
    uno, _ = _due_post_stessa_foto(db, archivio, campagna_in_revisione(db))
    assert _ritocca(client, uno, variante="spinta").status_code == 401


# --- Dopo l'approvazione ------------------------------------------------------------


def _post_approvato_con_foto(db, archivio, **opzioni):
    campagna = campagna_attiva(db)
    post = post_approvato(
        db,
        campagna_id=campagna.id,
        data_ora=datetime.now(timezone.utc) + timedelta(days=3),
    )
    foto = campagne.foto_per_id(db, [post.versione_corrente.legami_foto[0].foto_id])[0]
    _prepara_foto(db, archivio, foto, **opzioni)
    contenuti.rendi_foto_approvate(db, campagna.id)
    db.expire_all()
    return post


def test_dopo_l_approvazione_la_versione_nasce_approvata_e_con_il_render_nuovo(
    db, client, utente_di_prova, archivio
):
    operatore = utente_di_prova("operatore")
    post = _post_approvato_con_foto(db, archivio)
    render_prima = post.versione_corrente.legami_foto[0].render
    assert render_prima is not None

    risposta = _ritocca(client, post, variante="spinta")

    assert risposta.status_code == 200
    db.expire_all()
    nuova = _versioni(db, post)[-1]
    assert nuova.tipo_intervento == "ritocco_foto"
    legame = nuova.legami_foto[0]
    assert legame.ritocco == {"variante": "spinta"}
    assert legame.render is not None and legame.render != render_prima
    assert archivio.esiste_derivato(legame.foto_id, legame.render)
    # il render di prima non si cancella (§1.2)
    assert archivio.esiste_derivato(legame.foto_id, render_prima)
    approvazioni = db.scalars(
        select(Approvazione).where(Approvazione.versione_id == nuova.id)
    ).all()
    assert [(a.utente_id, a.esito) for a in approvazioni] == [
        (operatore.id, "approvato")
    ]


def test_i_byte_pubblicati_sono_quelli_del_render_nuovo(
    db, client, utente_di_prova, archivio
):
    from app.adapters.social import SocialFinto, usa_social
    from app.moduli.pubblicazione import service as pubblicazione

    utente_di_prova("operatore")
    post = _post_approvato_con_foto(db, archivio)
    _ritocca(client, post, variante="spinta")
    db.expire_all()
    legame = _versioni(db, post)[-1].legami_foto[0]
    atteso = archivio.leggi_derivato(legame.foto_id, legame.render)
    post.data_ora = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.flush()
    social = SocialFinto()
    with usa_social(social):
        pubblicazione.pubblica_dovuti(db, datetime.now(timezone.utc))
    assert social.foto_inviate and social.foto_inviate[0][0] == atteso


def test_dopo_l_approvazione_con_la_privacy_il_render_cambia(
    db, client, utente_di_prova, archivio
):
    utente_di_prova("operatore")
    post = _post_approvato_con_foto(db, archivio, zone=ZONE)
    prima = post.versione_corrente.legami_foto[0].render
    assert _ritocca(client, post, privacy=True).status_code == 200
    db.expire_all()
    dopo = _versioni(db, post)[-1].legami_foto[0]
    assert dopo.ritocco["privacy"] is True and dopo.render not in (None, prima)


def test_approvato_vicino_all_uscita_409(db, client, utente_di_prova, archivio):
    utente_di_prova("operatore")
    post = _post_approvato_con_foto(db, archivio)
    post.data_ora = datetime.now(timezone.utc) + timedelta(minutes=5)
    db.flush()
    assert _ritocca(client, post, variante="spinta").status_code == 409
