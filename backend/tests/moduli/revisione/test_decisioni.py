"""Test di nota interna, respingi e togli il canale.

Verifica i criteri di accettazione:
- CA-23: nota interna → stato invariato, decisione `nota`, nessuna email.
- CA-24: respingi senza motivo o nota → 422.
- CA-25: respingi `foto` con foto segnate → respinta, post scartati,
  notifica `campagna_respinta` all'artigiano.
- CA-53: togli il canale → i suoi post scartati, decisione con la nota;
  l'ultimo canale → 409.
"""

from datetime import datetime, timezone

from sqlalchemy import func, select

from app.moduli.campagne.models import DecisioneCampagna, Foto
from app.moduli.notifiche.models import Notifica
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_con_piano_da_rivedere,
    campagna_in_bozza,
    campagna_in_revisione,
    campagna_inviata,
)
from tests.moduli.contenuti.fabbrica import post_da_approvare

ADESSO = datetime(2026, 1, 10, 12, tzinfo=timezone.utc)


def _decisioni(db, campagna_id):
    return db.scalars(
        select(DecisioneCampagna)
        .where(DecisioneCampagna.campagna_id == campagna_id)
        .order_by(DecisioneCampagna.id)
    ).all()


def test_ca23_nota_interna_stato_invariato_e_nessuna_email(
    db, client, utente_di_prova, coda
):
    campagna = campagna_in_revisione(db)
    operatore = utente_di_prova("operatore")
    notifiche_prima = db.scalar(select(func.count(Notifica.id)))

    risposta = client.post(
        f"/api/campagne/{campagna.id}/nota", json={"nota": "Chiamare Mario."}
    )
    assert risposta.status_code == 200

    db.refresh(campagna)
    assert campagna.stato == "in_revisione"
    [decisione] = _decisioni(db, campagna.id)
    assert decisione.esito == "nota"
    assert decisione.nota == "Chiamare Mario."
    assert decisione.utente_id == operatore.id
    # Nessuna email e nessun job: la nota è solo interna (R-32).
    assert db.scalar(select(func.count(Notifica.id))) == notifiche_prima
    assert list(coda.jobs.values()) == []


def test_nota_su_bozza_409_e_vuota_422(db, client, utente_di_prova):
    bozza = campagna_in_bozza(db)
    inviata = campagna_inviata(db)
    utente_di_prova("operatore")

    assert (
        client.post(f"/api/campagne/{bozza.id}/nota", json={"nota": "x"}).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/campagne/{inviata.id}/nota", json={"nota": "   "}
        ).status_code
        == 422
    )
    assert _decisioni(db, inviata.id) == []


def test_ca24_respingi_senza_motivo_o_nota_422(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    utente_di_prova("operatore")

    assert (
        client.post(
            f"/api/campagne/{campagna.id}/respingi", json={"nota": "x"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/campagne/{campagna.id}/respingi",
            json={"motivo": "foto"},
        ).status_code
        == 422
    )
    db.refresh(campagna)
    assert campagna.stato == "in_revisione"


def test_ca25_respingi_foto_scarta_i_post_e_avvisa(db, client, utente_di_prova, coda):
    artigiano = utente(db, "artigiano")
    bottega = profilo(db, utente_id=artigiano.id)
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    post = post_da_approvare(db, campagna_id=campagna.id)
    altro = post_da_approvare(db, campagna_id=campagna.id, canale="facebook")
    segnate = list(
        db.scalars(select(Foto).where(Foto.campagna_id == campagna.id).limit(2))
    )
    utente_di_prova("operatore")

    risposta = client.post(
        f"/api/campagne/{campagna.id}/respingi",
        json={
            "motivo": "foto",
            "nota": "Le foto del banco sono troppo buie.",
            "foto_segnate": [f.id for f in segnate],
        },
    )
    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "respinta"}

    db.refresh(campagna)
    db.refresh(post)
    db.refresh(altro)
    assert campagna.stato == "respinta"
    assert campagna.chiusa_il is not None
    assert post.stato == "scartato"
    assert altro.stato == "scartato"

    [decisione] = _decisioni(db, campagna.id)
    assert decisione.esito == "respinta"
    assert decisione.motivo == "foto"
    assert decisione.nota == "Le foto del banco sono troppo buie."
    assert decisione.foto_segnate == [f.id for f in segnate]

    [notifica] = db.scalars(
        select(Notifica).where(Notifica.campagna_id == campagna.id)
    ).all()
    assert notifica.tipo == "campagna_respinta"
    assert notifica.utente_id == artigiano.id
    assert notifica.stato_invio == "da_inviare"
    job = next(j for j in coda.jobs.values() if j["task_name"] == "invia_notifica")
    contenuto = job["args"]["contenuto"]
    assert contenuto["titolo"] == campagna.titolo
    assert contenuto["motivo"] == "foto"
    assert contenuto["nota"] == "Le foto del banco sono troppo buie."
    assert {foto["nome"] for foto in contenuto["foto"]} == {f.file for f in segnate}
    assert {foto["mime"] for foto in contenuto["foto"]} == {f.mime for f in segnate}


def test_respingi_foto_di_altra_campagna_422(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    altra = campagna_inviata(db)
    foto_altrui = list(db.scalars(select(Foto).where(Foto.campagna_id == altra.id)))
    utente_di_prova("operatore")

    risposta = client.post(
        f"/api/campagne/{campagna.id}/respingi",
        json={
            "motivo": "foto",
            "nota": "Rifare.",
            "foto_segnate": [foto_altrui[0].id],
        },
    )
    assert risposta.status_code == 422
    db.refresh(campagna)
    assert campagna.stato == "in_revisione"


def test_respingi_da_piano_da_rivedere_e_stati_vietati(db, client, utente_di_prova):
    debole = campagna_con_piano_da_rivedere(db)
    attiva = campagna_inviata(db)
    attiva.stato = "attiva"
    db.flush()
    utente_di_prova("operatore")

    ok = client.post(
        f"/api/campagne/{debole.id}/respingi",
        json={"motivo": "altro", "nota": "Il piano non convince."},
    )
    assert ok.status_code == 200
    db.refresh(debole)
    assert debole.stato == "respinta"

    ko = client.post(
        f"/api/campagne/{attiva.id}/respingi",
        json={"motivo": "altro", "nota": "Troppo tardi."},
    )
    assert ko.status_code == 409


def test_ca53_togli_canale_scarta_i_suoi_post(db, client, utente_di_prova):
    bottega = profilo(db, canali=["instagram", "facebook"])
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    ig = post_da_approvare(db, campagna_id=campagna.id, canale="instagram")
    fb = post_da_approvare(db, campagna_id=campagna.id, canale="facebook")
    operatore = utente_di_prova("operatore")

    risposta = client.post(
        f"/api/campagne/{campagna.id}/togli-canale",
        json={"canale": "instagram", "nota": "Le foto non sono adatte."},
    )
    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "in_revisione"}

    db.refresh(campagna)
    db.refresh(ig)
    db.refresh(fb)
    assert campagna.canali_tolti == ["instagram"]
    assert ig.stato == "scartato"
    assert fb.stato == "da_approvare"

    [decisione] = _decisioni(db, campagna.id)
    assert decisione.esito == "canale_tolto"
    assert decisione.canale == "instagram"
    assert decisione.nota == "Le foto non sono adatte."
    assert decisione.utente_id == operatore.id


def test_ca53_ultimo_canale_409_e_noti_obbligatorie(db, client, utente_di_prova):
    bottega = profilo(db, canali=["instagram"])
    campagna = campagna_in_revisione(db, profilo_id=bottega.id)
    utente_di_prova("operatore")

    assert (
        client.post(
            f"/api/campagne/{campagna.id}/togli-canale",
            json={"canale": "instagram", "nota": "Via tutto."},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/campagne/{campagna.id}/togli-canale",
            json={"canale": "instagram", "nota": "  "},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/campagne/{campagna.id}/togli-canale",
            json={"canale": "tiktok", "nota": "No."},
        ).status_code
        == 422
    )
    db.refresh(campagna)
    assert campagna.canali_tolti in (None, [])


def test_togli_canale_da_generazione_fallita_riparte(db, client, utente_di_prova, coda):
    bottega = profilo(db, canali=["instagram", "facebook"])
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    campagna.stato = "generazione_fallita"
    db.flush()
    utente_di_prova("operatore")

    risposta = client.post(
        f"/api/campagne/{campagna.id}/togli-canale",
        json={"canale": "instagram", "nota": "Account Instagram scollegato."},
    )
    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "inviata"}

    db.refresh(campagna)
    assert campagna.stato == "inviata"
    assert campagna.canali_tolti == ["instagram"]
    job = [j for j in coda.jobs.values() if j["task_name"] == "genera_campagna"]
    assert job and job[-1]["args"] == {"campagna_id": campagna.id}


def test_togli_canale_da_attiva_409(db, client, utente_di_prova):
    bottega = profilo(db, canali=["instagram", "facebook"])
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    campagna.stato = "attiva"
    db.flush()
    utente_di_prova("operatore")

    assert (
        client.post(
            f"/api/campagne/{campagna.id}/togli-canale",
            json={"canale": "instagram", "nota": "No."},
        ).status_code
        == 409
    )


def test_decisioni_riservate_all_operatore_e_404(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    utente_di_prova("artigiano")

    assert (
        client.post(f"/api/campagne/{campagna.id}/nota", json={"nota": "x"}).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/campagne/{campagna.id}/respingi",
            json={"motivo": "altro", "nota": "x"},
        ).status_code
        == 403
    )

    utente_di_prova("operatore")
    for url in ("nota", "respingi", "togli-canale"):
        corpo = {"nota": "x"}
        if url == "respingi":
            corpo["motivo"] = "altro"
        if url == "togli-canale":
            corpo["canale"] = "instagram"
        assert client.post(f"/api/campagne/99999/{url}", json=corpo).status_code == 404
