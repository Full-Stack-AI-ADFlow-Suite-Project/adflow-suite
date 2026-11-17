"""Percorso completo delle uscite nello stesso giorno, attraverso le API.

Bozza con foto → generazione (AI finta) → vedi campagna → sposta un'uscita →
approva → il tick del worker pubblica. A ogni passo ogni uscita ha un post per
canale, tutti nello stesso giorno di Roma; i file hanno il nome leggibile.
"""

import re
from datetime import date, datetime, timedelta

import pytest

from app.core.orologio import ROMA

# Le fixture del percorso di revisione (finti, orologio, accessi, api, entra,
# lavora) e le sue funzioni di appoggio: stessi finti, stessa ora, stesso seed.
from tests.percorsi.test_percorso_revisione import (  # noqa: F401
    ARTIGIANO,
    DUE_CANALI,
    INIZIO,
    OPERATORE,
    UNA_SETTIMANA,
    _nuova_campagna,
    _post_piano,
    _tick,
    _vedi,
    accessi,
    api,
    entra,
    finti,
    lavora,
    orologio,
)


def _giorno(post: dict) -> date:
    return datetime.fromisoformat(post["data_ora"]).astimezone(ROMA).date()


def _controlla_uscite(vista: dict, canali=tuple(DUE_CANALI)) -> None:
    assert vista["uscite"], "il piano non ha uscite"
    for uscita in vista["uscite"]:
        assert sorted(p["canale"] for p in uscita["post"]) == sorted(canali), uscita
        assert len({_giorno(p) for p in uscita["post"]}) == 1, uscita


def _per_uscita(vista: dict) -> dict[int, dict[str, dict]]:
    return {u["numero"]: {p["canale"]: p for p in u["post"]} for u in vista["uscite"]}


@pytest.mark.parametrize("n_foto", [1, 3, 6])
@pytest.mark.parametrize("giorni", [7, 31])
def test_la_generazione_da_uscite_complete_nello_stesso_giorno(
    api, entra, lavora, n_foto, giorni
):
    campagna_id, _ = _nuova_campagna(
        api,
        entra,
        lavora,
        f"Prova {giorni}g {n_foto}f",
        INIZIO,
        INIZIO + timedelta(days=giorni - 1),
        n_foto=n_foto,
    )
    assert entra(OPERATORE)
    vista = _vedi(api, campagna_id)

    _controlla_uscite(vista)
    attesi = giorni * 3 // 7  # 3 post a settimana per canale (profilo del seed)
    for canale in DUE_CANALI:
        assert len([p for p in _post_piano(vista) if p["canale"] == canale]) == attesi
    # le uscite cadono dentro il periodo
    for p in _post_piano(vista):
        assert INIZIO <= _giorno(p) <= INIZIO + timedelta(days=giorni - 1)


def test_i_file_delle_foto_hanno_il_nome_della_bottega_e_non_si_ripetono(
    api, entra, lavora, finti
):
    _nuova_campagna(api, entra, lavora, "Nomi", INIZIO, UNA_SETTIMANA, n_foto=6)

    nomi = finti.archivio.file_salvati

    assert len(nomi) == len(set(nomi)) >= 6
    for nome in nomi:
        assert re.fullmatch(
            r"[a-z0-9-]+_\d{8}-\d{6}_[0-9a-f]{8}\.(jpg|png)", nome
        ), nome


def test_sposta_un_post_porta_l_uscita_poi_approva_e_pubblica_insieme(
    api, entra, lavora, orologio, finti
):
    campagna_id, _ = _nuova_campagna(
        api, entra, lavora, "Sposta", INIZIO, INIZIO + timedelta(days=20), n_foto=4
    )
    assert entra(OPERATORE)
    prima = _vedi(api, campagna_id)
    uscite = _per_uscita(prima)
    numero = sorted(uscite)[1]
    fb, ig = uscite[numero]["facebook"], uscite[numero]["instagram"]
    ora_fb = datetime.fromisoformat(fb["data_ora"]).astimezone(ROMA).time()
    ora_ig = datetime.fromisoformat(ig["data_ora"]).astimezone(ROMA).time()

    # 1. Si sposta Facebook a un giorno libero verso la fine, alle 18:45.
    nuovo_giorno = INIZIO + timedelta(days=19)
    nuovo = datetime.combine(
        nuovo_giorno, datetime.min.time().replace(hour=18, minute=45), tzinfo=ROMA
    )
    r = api(
        "POST", f"/post/{fb['post_id']}/sposta", json={"data_ora": nuovo.isoformat()}
    )
    assert r.status_code == 200, r.text
    dopo = _vedi(api, campagna_id)
    _controlla_uscite(dopo)
    spostata = _per_uscita(dopo)[numero]
    assert _giorno(spostata["facebook"]) == nuovo_giorno
    assert _giorno(spostata["instagram"]) == nuovo_giorno
    assert (
        datetime.fromisoformat(spostata["facebook"]["data_ora"]).astimezone(ROMA).time()
        == nuovo.time()
    )
    # Instagram ha tenuto la sua ora, solo il giorno è cambiato.
    assert (
        datetime.fromisoformat(spostata["instagram"]["data_ora"])
        .astimezone(ROMA)
        .time()
        == ora_ig
    )
    assert ora_fb is not None
    # Le altre uscite non si sono mosse.
    for n, due in _per_uscita(prima).items():
        if n != numero:
            assert {c: p["data_ora"] for c, p in due.items()} == {
                c: p["data_ora"] for c, p in _per_uscita(dopo)[n].items()
            }

    # 2. Solo l'ora: Instagram non si muove, e Facebook neppure di giorno.
    stesso_giorno = datetime.combine(
        nuovo_giorno, datetime.min.time().replace(hour=9), tzinfo=ROMA
    )
    r = api(
        "POST",
        f"/post/{ig['post_id']}/sposta",
        json={"data_ora": stesso_giorno.isoformat()},
    )
    assert r.status_code == 200, r.text
    ora_sola = _per_uscita(_vedi(api, campagna_id))[numero]
    assert (
        _giorno(ora_sola["facebook"]) == _giorno(ora_sola["instagram"]) == nuovo_giorno
    )
    assert (
        datetime.fromisoformat(ora_sola["facebook"]["data_ora"]).astimezone(ROMA).time()
        == nuovo.time()
    )

    # 3. Fuori periodo: 422 e niente cambia.
    fuori = datetime.combine(
        INIZIO + timedelta(days=40), datetime.min.time().replace(hour=10), tzinfo=ROMA
    )
    r = api(
        "POST", f"/post/{fb['post_id']}/sposta", json={"data_ora": fuori.isoformat()}
    )
    assert r.status_code == 422
    assert _per_uscita(_vedi(api, campagna_id))[numero] == ora_sola

    # 4. Si approva e, dopo l'approvazione, si sposta di nuovo: l'uscita segue ancora.
    assert api("POST", f"/campagne/{campagna_id}/approva").status_code == 200
    altro_giorno = INIZIO + timedelta(days=10)
    nuovo2 = datetime.combine(
        altro_giorno, datetime.min.time().replace(hour=12), tzinfo=ROMA
    )
    r = api(
        "POST", f"/post/{ig['post_id']}/sposta", json={"data_ora": nuovo2.isoformat()}
    )
    assert r.status_code == 200, r.text
    approvata = _vedi(api, campagna_id)
    _controlla_uscite(approvata)
    assert _giorno(_per_uscita(approvata)[numero]["facebook"]) == altro_giorno
    assert all(p["stato"] == "approvato" for p in _post_piano(approvata))

    # 5. Il tempo passa: i due post dell'uscita escono lo stesso giorno, ciascuno alla sua ora.
    orologio.ora = datetime.combine(
        altro_giorno + timedelta(days=1), datetime.min.time(), tzinfo=ROMA
    )
    _tick()
    assert entra(OPERATORE)  # la sessione è scaduta con l'avanzamento
    uscite_fatte = [
        p for p in _post_piano(_vedi(api, campagna_id)) if p["stato"] == "pubblicato"
    ]
    per_canale = {p["canale"] for p in uscite_fatte if _giorno(p) == altro_giorno}
    assert per_canale == set(DUE_CANALI)
    assert len(finti.social.pubblicazioni) == len(uscite_fatte)


def test_senza_nessuna_foto_tutte_le_uscite_hanno_immagini_ai_nello_stesso_giorno(
    api, entra, lavora
):
    assert entra(ARTIGIANO)
    campagna_id = api(
        "POST",
        "/campagne",
        json={
            "titolo": "Senza foto",
            "inizio": INIZIO.isoformat(),
            "fine": (INIZIO + timedelta(days=13)).isoformat(),
            "canali": DUE_CANALI,
        },
    ).json()["id"]
    assert (
        api(
            "POST", f"/campagne/{campagna_id}/invia", json={"dichiarazione": True}
        ).status_code
        == 200
    )
    assert lavora()
    assert entra(OPERATORE)
    vista = _vedi(api, campagna_id)

    _controlla_uscite(vista)
    assert {p["riempitivo"] for p in _post_piano(vista)} == {"immagine_ai"}


def test_una_campagna_con_un_solo_canale_ha_uscite_di_un_post(api, entra, lavora):
    """Con un solo canale l'uscita ha un post: la regola «uno per canale» regge."""
    assert entra(ARTIGIANO)
    campagna_id = api(
        "POST",
        "/campagne",
        json={
            "titolo": "Solo Instagram",
            "inizio": INIZIO.isoformat(),
            "fine": UNA_SETTIMANA.isoformat(),
            "canali": ["instagram"],
        },
    ).json()["id"]
    assert (
        api(
            "POST", f"/campagne/{campagna_id}/invia", json={"dichiarazione": True}
        ).status_code
        == 200
    )
    assert lavora()
    assert entra(OPERATORE)
    vista = _vedi(api, campagna_id)

    _controlla_uscite(vista, canali=("instagram",))


def test_due_campagne_sovrapposte_evitano_gli_stessi_orari_senza_rompere_le_uscite(
    api, entra, lavora
):
    a, _ = _nuova_campagna(api, entra, lavora, "A", INIZIO, INIZIO + timedelta(days=13))
    assert entra(OPERATORE)
    assert api("POST", f"/campagne/{a}/approva").status_code == 200
    b, _ = _nuova_campagna(api, entra, lavora, "B", INIZIO, INIZIO + timedelta(days=13))
    assert entra(OPERATORE)

    va, vb = _vedi(api, a), _vedi(api, b)

    _controlla_uscite(va)
    _controlla_uscite(vb)
    occupati = {
        (p["canale"], datetime.fromisoformat(p["data_ora"]).astimezone(ROMA))
        for p in _post_piano(va)
    }
    for p in _post_piano(vb):
        chiave = (p["canale"], datetime.fromisoformat(p["data_ora"]).astimezone(ROMA))
        assert chiave not in occupati, f"stesso canale e stessa ora di A: {chiave}"
