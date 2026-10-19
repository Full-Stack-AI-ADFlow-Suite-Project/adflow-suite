"""T3-66: il percorso della corsia 6 (ADR-116), dalle API alla pubblicazione (CA-91).

Due percorsi con le API vere, gli utenti del seed, il job di generazione e il
tick di pubblicazione, come nelle altre chiusure; AI, social e archivio sono
quelli finti. Il primo: la richiesta all'artigiano, la foto nuova, Cambia foto,
Approva e la pubblicazione con la foto nuova. Il secondo: gli interventi dopo
l'approvazione (modifica, sposta, annulla il post, sospendi, riattiva) e il
tick che pubblica ciò che resta.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import select

from app import worker
from app.moduli.campagne.models import Foto
from app.moduli.revisione.models import Approvazione
from tests.percorsi.test_percorso_sprint1 import (
    ARTIGIANO,
    OPERATORE,
    UNA_SETTIMANA,
    _bozza,
    _carica,
    _foto_del_post,
    _foto_jpeg,
    _post_per_canale,
    _stato,
    _vedi,
    accessi,
    api,
    entra,
    finti,
    lavora,
    orologio,
)

__all__ = ["accessi", "api", "entra", "finti", "lavora", "orologio"]  # le fixture


def _in_revisione(api, entra, lavora) -> tuple[int, list[int]]:
    """Una campagna di 7 giorni con 4 foto in 2 gruppi, generata e in revisione."""
    entra(ARTIGIANO)
    campagna, foto = _bozza(api, UNA_SETTIMANA, foto_per_gruppo=(2, 2))
    invio = api("POST", f"/campagne/{campagna}/invia", json={"dichiarazione": True})
    assert invio.status_code == 200, invio.text
    assert lavora() == [1]
    entra(OPERATORE)
    assert _stato(api, campagna) == "in_revisione"
    return campagna, foto


def _ok(risposta, codice=200):
    assert risposta.status_code == codice, risposta.text
    return risposta.json()


def _gruppo_di(api, campagna: int) -> dict[int, int]:
    """Per ogni foto della campagna, il suo gruppo."""
    gruppi = api("GET", f"/campagne/{campagna}").json()["gruppi"]
    return {f["id"]: g["id"] for g in gruppi for f in g["foto"]}


def test_ca91_richiesta_cambia_foto_approva_pubblica(
    api, entra, lavora, orologio, finti, db
):
    campagna, foto = _in_revisione(api, entra, lavora)
    gruppo_di = _gruppo_di(api, campagna)

    # Su Instagram una foto resta libera: il post scelto è nel suo stesso gruppo,
    # così Cambia foto ha già una scelta oltre alla foto che arriva dall'artigiano.
    instagram = _post_per_canale(_vedi(api, campagna))["instagram"]
    usate = {f for uno in instagram for f in _foto_del_post(uno)}
    [libera] = set(foto) - usate
    post = next(
        uno
        for uno in instagram
        if gruppo_di[_foto_del_post(uno)[0]] == gruppo_di[libera]
    )
    vecchia = _foto_del_post(post)[0]

    # L'operatore chiede una foto nuova al posto di quella del post.
    richiesta = _ok(
        api(
            "POST",
            f"/campagne/{campagna}/richiesta",
            json={"domanda": "Puoi mandarne una senza persone?", "foto": [vecchia]},
        ),
        201,
    )
    assert richiesta["stato"] == "aperta"
    assert _stato(api, campagna) == "in_revisione"

    # L'artigiano la vede per prima, carica la foto nuova con la dichiarazione e risponde.
    entra(ARTIGIANO)
    [prima, *_] = api("GET", "/campagne").json()
    assert (prima["id"], prima["richiesta"]) == (campagna, "aperta")
    nuova = _ok(
        api(
            "POST",
            f"/campagne/{campagna}/richiesta/foto",
            files={"file": ("nuova.jpg", _foto_jpeg(250), "image/jpeg")},
            data={"foto_id": str(vecchia), "dichiarazione": "true"},
        ),
        201,
    )
    inviata = _ok(
        api(
            "POST",
            f"/campagne/{campagna}/richiesta/invia",
            json={"risposta": "Ecco la foto senza persone."},
        )
    )
    assert inviata["stato"] == "inviata"
    assert inviata["foto"][0]["nuova_foto_id"] == nuova["id"]

    # L'operatore vede la risposta, trova la foto nuova in cima, la usa e approva.
    entra(OPERATORE)
    [riga] = [r for r in api("GET", "/da-approvare").json() if r["id"] == campagna]
    assert riga["richiesta"] == "inviata"
    possibili = _ok(api("GET", f"/post/{post['post_id']}/foto-possibili"))
    assert [(f["foto_id"], f["analizzata"]) for f in possibili] == [
        (nuova["id"], False),
        (libera, True),
    ]
    _ok(
        api(
            "POST",
            f"/post/{post['post_id']}/cambia-foto",
            json={"foto_id": nuova["id"]},
        )
    )
    cambiato = next(
        uno
        for u in _vedi(api, campagna)["uscite"]
        for uno in u["post"]
        if uno["post_id"] == post["post_id"]
    )
    assert cambiato["versione_corrente"]["tipo_intervento"] == "cambio_foto"
    assert _foto_del_post(cambiato) == [nuova["id"]]
    assert cambiato["stato"] == "da_approvare"
    _ok(api("POST", f"/campagne/{campagna}/approva"))

    # Il tick pubblica il post con la foto nuova.
    orologio.dopo(UNA_SETTIMANA)
    worker.tick_pubblicazione(0)
    assert len(finti.social.pubblicazioni) == 6
    db.expire_all()
    assert "instagram" in db.get(Foto, nuova["id"]).pubblicata_su
    assert "instagram" not in db.get(Foto, vecchia).pubblicata_su


def test_ca91_dopo_l_approvazione_modifica_sposta_annulla_sospendi_riattiva(
    api, entra, lavora, orologio, finti, db
):
    campagna, _ = _in_revisione(api, entra, lavora)
    _ok(api("POST", f"/campagne/{campagna}/approva"))
    assert _stato(api, campagna) == "attiva"

    facebook = sorted(
        _post_per_canale(_vedi(api, campagna))["facebook"],
        key=lambda uno: uno["data_ora"],
    )
    primo, secondo, terzo = facebook
    assert all(
        set(uno["interventi"]) == {"modifica", "cambia_foto", "sposta", "annulla"}
        for uno in facebook
    )

    # Modifica il primo: la versione nuova nasce approvata dall'operatore.
    testo = "Testo corretto dopo l'approvazione."
    _ok(
        api(
            "POST",
            f"/post/{primo['post_id']}/modifica",
            json={"testo": testo, "hashtag": []},
        )
    )
    db.expire_all()
    versione = db.scalars(select(Approvazione).order_by(Approvazione.id.desc())).first()
    assert versione is not None and versione.ruolo == "operatore"

    # Sposta il secondo di un'ora.
    vecchia_data = _data(secondo["data_ora"])
    nuova_data = vecchia_data + timedelta(hours=1)
    _ok(
        api(
            "POST",
            f"/post/{secondo['post_id']}/sposta",
            json={"data_ora": nuova_data.isoformat()},
        )
    )

    # Annulla il terzo con la nota: la campagna resta attiva.
    annullato = _ok(
        api(
            "POST",
            f"/post/{terzo['post_id']}/annulla",
            json={"nota": "Il pezzo è esaurito."},
        )
    )
    assert annullato == {"stato": "annullato"}
    assert _stato(api, campagna) == "attiva"

    # Sospendi con una nota e riattiva: niente arretrati, tutto resta com'è.
    _ok(api("POST", f"/campagne/{campagna}/sospendi", json={"nota": "Ferie."}))
    assert _stato(api, campagna) == "sospesa"
    _ok(api("POST", f"/campagne/{campagna}/riattiva", json={"pubblica_ora": []}))
    assert _stato(api, campagna) == "attiva"
    decisioni = api("GET", f"/campagne/{campagna}").json()["decisioni"]
    assert [d["esito"] for d in decisioni if d["esito"] != "approvata"] == [
        "riprogrammato",
        "post_annullato",
        "sospesa",
        "riattivata",
    ]

    def stati() -> dict[int, str]:
        entra(OPERATORE)
        return {
            uno["post_id"]: uno["stato"]
            for u in _vedi(api, campagna)["uscite"]
            for uno in u["post"]
        }

    # Alla vecchia data il secondo non esce ancora; il primo esce con la versione nuova.
    orologio.ora = vecchia_data + timedelta(minutes=30)
    worker.tick_pubblicazione(0)
    dopo_vecchia = stati()
    assert dopo_vecchia[primo["post_id"]] == "pubblicato"
    assert dopo_vecchia[secondo["post_id"]] == "approvato"
    assert any(testo in uscito["testo"] for uscito in finti.social.pubblicazioni)

    # Alla data nuova esce il secondo.
    orologio.ora = nuova_data + timedelta(minutes=1)
    worker.tick_pubblicazione(0)
    assert stati()[secondo["post_id"]] == "pubblicato"

    # In fondo esce tutto tranne il terzo.
    orologio.dopo(UNA_SETTIMANA)
    worker.tick_pubblicazione(0)
    finali = stati()
    assert finali[terzo["post_id"]] == "annullato"
    assert sorted(set(finali.values())) == ["annullato", "pubblicato"]
    assert len(finti.social.pubblicazioni) == 5


def _data(testo: str) -> datetime:
    return datetime.fromisoformat(testo)
