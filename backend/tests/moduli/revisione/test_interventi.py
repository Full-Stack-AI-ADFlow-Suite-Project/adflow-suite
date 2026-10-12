"""Test degli endpoint degli interventi sul post (T2b-42, spec R-03, R-30, R-31, R-34)."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.moduli.campagne.models import DecisioneCampagna
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_in_revisione,
    campagna_sospesa,
)
from tests.moduli.contenuti.fabbrica import (
    post_approvato,
    post_da_approvare,
    post_fallito,
)

DENTRO = "2030-01-10T12:00:00+00:00"
FUORI = "2030-02-10T12:00:00+00:00"
PASSATO = "2020-01-10T12:00:00+00:00"


def _post_di_prova(db, campagna, **campi):
    return post_da_approvare(db, campagna_id=campagna.id, **campi)


def test_ca64_modifica_nasce_una_versione_con_autore_e_foto_uguali(
    db, client, utente_di_prova
):
    """Versione `modifica_operatore` validata, cicli invariati, spunta azzerata."""
    campagna = campagna_in_revisione(db)
    post = _post_di_prova(db, campagna)
    operatore = utente_di_prova("operatore")
    post.controllato_da = operatore.id
    post.controllato_il = datetime.now(timezone.utc)
    db.flush()

    risposta = client.post(
        f"/api/post/{post.id}/modifica",
        json={
            "testo": "Testo corretto a mano",
            "hashtag": ["#fattoamano", "  bottega  "],
        },
    )
    assert risposta.status_code == 200

    db.refresh(post)
    assert len(post.versioni) == 2
    nuova = post.versione_corrente
    assert nuova.tipo_intervento == "modifica_operatore"
    assert nuova.autore_id == operatore.id
    assert nuova.testo == "Testo corretto a mano"
    assert nuova.hashtag == ["fattoamano", "bottega"]
    assert nuova.errori_validazione is not None
    # Stesse foto della versione precedente e nessun ciclo di rigenerazione.
    assert {l.foto_id for l in nuova.legami_foto} == {
        l.foto_id for l in post.versioni[0].legami_foto
    }
    assert post.n_rigenerazioni_testo == 0
    # La nuova versione azzera la spunta «va bene» (R-30).
    assert post.controllato_da is None
    assert post.controllato_il is None


def test_ca64_modifica_uguale_o_con_blocco_422_nessuna_versione(
    db, client, utente_di_prova
):
    campagna = campagna_in_revisione(db)
    post = _post_di_prova(db, campagna)
    utente_di_prova("operatore")

    uguale = client.post(
        f"/api/post/{post.id}/modifica",
        json={"testo": "Testo di prova", "hashtag": ["artigianato"]},
    )
    assert uguale.status_code == 422

    bloccata = client.post(
        f"/api/post/{post.id}/modifica",
        json={"testo": "Tutto a 10€ solo oggi", "hashtag": []},
    )
    assert bloccata.status_code == 422

    db.refresh(post)
    assert len(post.versioni) == 1


def test_ca65_spunta_salva_chi_e_quando_e_si_toglie(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    post = _post_di_prova(db, campagna)
    operatore = utente_di_prova("operatore")

    assert (
        client.post(
            f"/api/post/{post.id}/controllato", json={"valore": True}
        ).status_code
        == 200
    )
    db.refresh(post)
    assert post.controllato_da == operatore.id
    assert post.controllato_il is not None

    assert (
        client.post(
            f"/api/post/{post.id}/controllato", json={"valore": False}
        ).status_code
        == 200
    )
    db.refresh(post)
    assert post.controllato_da is None
    assert post.controllato_il is None


def test_ca65_spunta_su_un_post_da_rivedere_409(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    post = _post_di_prova(db, campagna, da_rivedere=True)
    utente_di_prova("operatore")

    assert (
        client.post(
            f"/api/post/{post.id}/controllato", json={"valore": True}
        ).status_code
        == 409
    )


def test_ca26_rigenera_da_zero_accende_intervento_e_accoda(
    db, client, utente_di_prova, coda
):
    campagna = campagna_in_revisione(db)
    post = _post_di_prova(db, campagna)
    utente_di_prova("operatore")

    risposta = client.post(f"/api/post/{post.id}/rigenera", json={"modalita": "totale"})
    assert risposta.status_code == 200

    db.refresh(post)
    assert post.intervento_in_corso == "rigenera_totale"
    assert post.intervento_dal is not None

    [job] = list(coda.jobs.values())
    assert job["task_name"] == "rigenera_post"
    assert job["args"] == {"post_id": post.id, "testo_proposto": None, "nota": None}


def test_ca27_rigenera_da_proposta_senza_testo_422_con_testo_accoda(
    db, client, utente_di_prova, coda
):
    campagna = campagna_in_revisione(db)
    post = _post_di_prova(db, campagna)
    utente_di_prova("operatore")

    senza = client.post(
        f"/api/post/{post.id}/rigenera", json={"modalita": "da_proposta"}
    )
    assert senza.status_code == 422
    db.refresh(post)
    assert post.intervento_in_corso is None
    assert list(coda.jobs.values()) == []

    risposta = client.post(
        f"/api/post/{post.id}/rigenera",
        json={
            "modalita": "da_proposta",
            "testo_proposto": "  Bozza scritta dall'operatore  ",
            "nota": "Più corto",
        },
    )
    assert risposta.status_code == 200

    db.refresh(post)
    assert post.intervento_in_corso == "rigenera_da_proposta"
    [job] = list(coda.jobs.values())
    assert job["args"] == {
        "post_id": post.id,
        "testo_proposto": "Bozza scritta dall'operatore",
        "nota": "Più corto",
    }


def test_ca28_quarta_rigenerazione_409_ma_la_modifica_resta(
    db, client, utente_di_prova
):
    campagna = campagna_in_revisione(db)
    post = _post_di_prova(db, campagna, n_rigenerazioni_testo=3)
    utente_di_prova("operatore")

    assert (
        client.post(
            f"/api/post/{post.id}/rigenera", json={"modalita": "totale"}
        ).status_code
        == 409
    )
    # Dopo 3 rigenerazioni la modifica a mano resta ammessa (R-03).
    assert (
        client.post(
            f"/api/post/{post.id}/modifica",
            json={"testo": "Modifica dopo tre cicli", "hashtag": []},
        ).status_code
        == 200
    )


def test_ca29_in_campagna_attiva_o_sospesa_gli_interventi_409(
    db, client, utente_di_prova
):
    attiva = campagna_attiva(db)
    post_attiva = post_approvato(db, campagna_id=attiva.id)
    sospesa = campagna_sospesa(db)
    post_sospesa = post_approvato(db, campagna_id=sospesa.id)
    utente_di_prova("operatore")

    for post in (post_attiva, post_sospesa):
        assert (
            client.post(
                f"/api/post/{post.id}/modifica",
                json={"testo": "Altro testo", "hashtag": []},
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"/api/post/{post.id}/controllato", json={"valore": True}
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"/api/post/{post.id}/rigenera", json={"modalita": "totale"}
            ).status_code
            == 409
        )


def test_ca31_un_secondo_intervento_409_e_dopo_10_minuti_si_rilancia(
    db, client, utente_di_prova, coda
):
    campagna = campagna_in_revisione(db)
    post = _post_di_prova(
        db,
        campagna,
        intervento_in_corso="rigenera_totale",
        intervento_dal=datetime.now(timezone.utc) - timedelta(minutes=2),
    )
    utente_di_prova("operatore")

    assert (
        client.post(
            f"/api/post/{post.id}/rigenera", json={"modalita": "totale"}
        ).status_code
        == 409
    )
    assert list(coda.jobs.values()) == []

    post.intervento_dal = datetime.now(timezone.utc) - timedelta(minutes=11)
    db.flush()
    assert (
        client.post(
            f"/api/post/{post.id}/rigenera", json={"modalita": "totale"}
        ).status_code
        == 200
    )
    db.refresh(post)
    assert post.intervento_dal is not None
    assert len(coda.jobs.values()) == 1


def test_ca66_intervento_vecchio_non_blocca_l_approvazione(db, client, utente_di_prova):
    """Intervento partito da più di 10 minuti: approva ammesso (R-31)."""
    campagna = campagna_in_revisione(db)
    post_da_approvare(
        db,
        campagna_id=campagna.id,
        intervento_in_corso="rigenera_totale",
        intervento_dal=datetime.now(timezone.utc) - timedelta(minutes=11),
    )
    utente_di_prova("operatore")

    assert client.post(f"/api/campagne/{campagna.id}/approva").status_code == 200


def test_ca67_riprogramma_dentro_il_periodo_torna_approvato(
    db, client, utente_di_prova
):
    campagna = campagna_attiva(db)
    post = post_fallito(db, campagna_id=campagna.id)
    operatore = utente_di_prova("operatore")

    risposta = client.post(
        f"/api/post/{post.id}/riprogramma", json={"data_ora": DENTRO}
    )
    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "approvato"}

    db.refresh(post)
    assert post.stato == "approvato"
    assert post.data_ora == datetime(2030, 1, 10, 12, tzinfo=timezone.utc)

    decisione = db.scalar(
        select(DecisioneCampagna).where(DecisioneCampagna.campagna_id == campagna.id)
    )
    assert decisione.esito == "riprogrammato"
    assert decisione.utente_id == operatore.id
    assert decisione.post_id == post.id


def test_ca67_riprogramma_fuori_periodo_o_nel_passato_422(db, client, utente_di_prova):
    campagna = campagna_attiva(db)
    post = post_fallito(db, campagna_id=campagna.id)
    utente_di_prova("operatore")

    for data_ora in (FUORI, PASSATO):
        assert (
            client.post(
                f"/api/post/{post.id}/riprogramma", json={"data_ora": data_ora}
            ).status_code
            == 422
        )
    db.refresh(post)
    assert post.stato == "fallito"
    assert (
        db.scalar(
            select(DecisioneCampagna).where(
                DecisioneCampagna.campagna_id == campagna.id
            )
        )
        is None
    )


def test_ca67_riprogramma_post_non_fallito_409(db, client, utente_di_prova):
    campagna = campagna_attiva(db)
    post = post_approvato(db, campagna_id=campagna.id)
    utente_di_prova("operatore")

    assert (
        client.post(
            f"/api/post/{post.id}/riprogramma", json={"data_ora": DENTRO}
        ).status_code
        == 409
    )


def test_riprogramma_anche_in_campagna_sospesa(db, client, utente_di_prova):
    campagna = campagna_sospesa(db)
    post = post_fallito(db, campagna_id=campagna.id)
    utente_di_prova("operatore")

    assert (
        client.post(
            f"/api/post/{post.id}/riprogramma", json={"data_ora": DENTRO}
        ).status_code
        == 200
    )
    db.refresh(post)
    assert post.stato == "approvato"


def test_interventi_permessi_e_post_inesistente(db, client, utente_di_prova):
    """L'artigiano non entra (403); un post che non c'è dà 404."""
    campagna = campagna_in_revisione(db)
    post = _post_di_prova(db, campagna)

    utente_di_prova("artigiano")
    for percorso in ("modifica", "controllato", "rigenera", "riprogramma"):
        assert (
            client.post(f"/api/post/{post.id}/{percorso}", json={}).status_code == 403
        )

    utente_di_prova("operatore")
    assert (
        client.post(
            "/api/post/99999/modifica",
            json={"testo": "Testo", "hashtag": []},
        ).status_code
        == 404
    )
    assert (
        client.post("/api/post/99999/controllato", json={"valore": True}).status_code
        == 404
    )
    assert (
        client.post("/api/post/99999/rigenera", json={"modalita": "totale"}).status_code
        == 404
    )
    assert (
        client.post(
            "/api/post/99999/riprogramma", json={"data_ora": DENTRO}
        ).status_code
        == 404
    )
