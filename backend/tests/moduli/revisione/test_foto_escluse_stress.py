"""Prova dura delle foto escluse: su campagne a caso ogni foto è usata oppure
compare una sola volta tra le escluse, con la causa che le spetta."""

import random

import pytest

from tests.moduli.campagne.fabbrica import campagna_in_revisione, foto
from tests.moduli.contenuti.fabbrica import post_da_approvare
from tests.moduli.revisione.test_router import _dettaglio


def _analisi(rng: random.Random, altre_foto: list[int]) -> dict:
    scelta = rng.randrange(7)
    if scelta == 0:
        return {}
    if scelta == 1:
        return {"idonea": False, "motivo": "Sfocata", "simile_a": None}
    if scelta == 2:  # non idonea e anche doppione: vale la non idoneità
        return {
            "idonea": False,
            "motivo": "Buia",
            "simile_a": rng.choice(altre_foto or [1]),
        }
    if scelta == 3:
        return {
            "idonea": True,
            "punteggio": rng.randrange(1, 6),
            "simile_a": rng.choice(altre_foto or [1]),
        }
    if scelta == 4:
        return {"idonea": True, "punteggio": rng.randrange(1, 6), "simile_a": None}
    if scelta == 5:
        return {"prompt": "una scena", "versione_prompt": "immagine_v3"}
    return {"idonea": None}


@pytest.mark.parametrize("seme", range(25))
def test_ogni_foto_e_usata_o_esclusa_una_volta_con_la_causa_giusta(
    db, client, utente_di_prova, seme
):
    rng = random.Random(seme)
    campagna = campagna_in_revisione(db)
    n_post = rng.randrange(1, 4)
    for _ in range(n_post):
        post_da_approvare(db, campagna_id=campagna.id)
    tutte = [foto(db, campagna=campagna) for _ in range(rng.randrange(0, 12))]
    ids = [f.id for f in tutte]
    for f in tutte:
        f.analisi_ai = _analisi(rng, [i for i in ids if i != f.id])
        if rng.random() < 0.15:
            f.origine = "creata_ai"
    db.flush()
    utente_di_prova("operatore")

    dati = _dettaglio(client, campagna.id).json()

    usate = {
        f["foto_id"]
        for u in dati["uscite"]
        for p in u["post"]
        for v in p["versioni"]
        for f in v["foto"]
    }
    escluse = [f for g in dati["foto_non_usate"] for f in g["foto"]]
    id_escluse = [f["foto_id"] for f in escluse]
    assert len(id_escluse) == len(set(id_escluse)), "una foto esclusa due volte"
    assert not usate & set(id_escluse), "una foto è insieme usata ed esclusa"
    per_id = {f.id: f for f in tutte}
    for e in escluse:
        f = per_id.get(e["foto_id"])
        if f is None:
            continue  # la foto di un post fabbricato dalla fabbrica
        analisi = f.analisi_ai or {}
        if f.origine != "caricata":
            atteso = "altro"
        elif analisi.get("idonea") is False:
            atteso = "non_idonea"
        elif analisi.get("simile_a"):
            atteso = "doppione"
        elif not analisi:
            atteso = "non_analizzata"
        elif analisi.get("idonea") is True:
            atteso = "in_eccesso"
        else:
            atteso = "altro"
        assert e["causa"] == atteso, (seme, e, analisi)
        assert (e["simile_a"] is not None) is (atteso == "doppione")
    # Tutte le foto aggiunte qui non sono in nessun post: devono essere tutte escluse.
    assert {f.id for f in tutte} <= set(id_escluse)
