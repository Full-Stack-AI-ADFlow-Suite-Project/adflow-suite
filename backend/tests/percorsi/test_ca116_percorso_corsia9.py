"""T3-927: il percorso della corsia 9 (ADR-119), CA-116, dalle API all'approvazione.

Le API vere, gli utenti del seed e i job presi dalla coda, come nelle altre
chiusure; AI, social e archivio sono quelli finti, nessuna chiamata reale.
L'artigiano invia due campagne sovrapposte della stessa bottega, di una
settimana (la durata di «1 settimana»); l'operatore, in revisione, fa «Rifai il
post» su un post con foto (una foto della campagna e il testo riscritto) e
«Rigenera immagine» su un post con un'immagine AI, poi approva le due campagne.
Lo storico dell'AI ha le chiamate di tutte e due le campagne e un voto.
"""

from app.adapters.ai import AIFinto
from app.core.coda import RIGENERA_IMMAGINE, RIGENERA_POST
from app.moduli.contenuti import jobs
from tests.percorsi.test_percorso_sprint1 import (
    ARTIGIANO,
    INIZIO,
    OPERATORE,
    UNA_SETTIMANA,
    _bozza,
    _foto_del_post,
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


def _ok(risposta, codice=200):
    assert risposta.status_code == codice, risposta.text
    return risposta.json()


def _invia(api, campagna: int) -> None:
    _ok(api("POST", f"/campagne/{campagna}/invia", json={"dichiarazione": True}))


def _esegui_rigenerazioni(coda, visti: set[int]) -> list[str]:
    """Esegue, una volta, i job di rigenerazione in coda: testo e immagine."""
    fatti = []
    for id_job, job in list(coda.jobs.items()):
        if id_job in visti:
            continue
        visti.add(id_job)
        args = job["args"]
        if job["task_name"] == RIGENERA_POST:
            assert not jobs.esegui_rigenerazione(
                args["post_id"], args["testo_proposto"], args["nota"], 1
            )
        elif job["task_name"] == RIGENERA_IMMAGINE:
            assert not jobs.esegui_rigenerazione_immagine(
                args["post_id"],
                args["nota"],
                args["riscrivi_testo"],
                args["nota_testo"],
                1,
            )
        else:
            continue
        fatti.append(job["task_name"])
    return fatti


def _post(api, campagna: int, post_id: int) -> dict:
    return next(
        uno
        for uscita in _vedi(api, campagna)["uscite"]
        for uno in uscita["post"]
        if uno["post_id"] == post_id
    )


def _orari(api, campagna: int) -> set[tuple[str, str]]:
    return {
        (uno["canale"], uno["data_ora"])
        for per_canale in _post_per_canale(_vedi(api, campagna)).values()
        for uno in per_canale
    }


def test_ca116_campagne_sovrapposte_rifai_il_post_rigenera_immagine_approva_storico(
    api, entra, lavora, orologio, finti, coda, db
):
    # 1. L'artigiano invia due campagne di una settimana nello stesso periodo.
    entra(ARTIGIANO)
    assert (UNA_SETTIMANA - INIZIO).days + 1 == 7  # «1 settimana»: fine = inizio + 6
    prima, foto = _bozza(api, UNA_SETTIMANA, foto_per_gruppo=(2, 2))
    assert _ok(api("GET", f"/campagne/{prima}"))["avvisi"] == []
    _invia(api, prima)

    # Una sola bozza per volta, ma con la prima inviata se ne può aprire un'altra
    # nello stesso periodo: il dettaglio lo dice (R-12, ADR-119).
    seconda, _ = _bozza(api, UNA_SETTIMANA, foto_per_gruppo=(1,))
    assert "campagne_sovrapposte" in _ok(api("GET", f"/campagne/{seconda}"))["avvisi"]
    _invia(api, seconda)
    assert "campagne_sovrapposte" in _ok(api("GET", f"/campagne/{prima}"))["avvisi"]

    assert lavora() == [1, 1]
    visti = set(coda.jobs)  # i job di generazione li ha già eseguiti lavora()
    entra(OPERATORE)
    assert (_stato(api, prima), _stato(api, seconda)) == ("in_revisione",) * 2

    # Il piano della seconda evita gli orari già occupati dalla prima (T3-922).
    assert not (_orari(api, prima) & _orari(api, seconda))

    # 2. Rifai il post su un post con foto della prima: una foto della campagna e
    #    il testo riscritto in un solo passaggio.
    instagram = _post_per_canale(_vedi(api, prima))["instagram"]
    usate = {f for uno in instagram for f in _foto_del_post(uno)}
    [libera] = set(foto) - usate
    gruppi = api("GET", f"/campagne/{prima}").json()["gruppi"]
    gruppo_di = {f["id"]: g["id"] for g in gruppi for f in g["foto"]}
    scelto = next(
        uno
        for uno in instagram
        if gruppo_di[_foto_del_post(uno)[0]] != gruppo_di[libera]
    )
    vecchia = _foto_del_post(scelto)[0]
    testo_prima = scelto["versione_corrente"]["testo"]
    possibili = _ok(api("GET", f"/post/{scelto['post_id']}/foto-possibili"))
    assert [(f["foto_id"], f["provenienza"]) for f in possibili] == [
        (libera, "campagna")
    ]

    _ok(
        api(
            "POST",
            f"/post/{scelto['post_id']}/cambia-foto",
            json={
                "foto_id": libera,
                "riscrivi_testo": True,
                "nota": "Parla della foto nuova.",
            },
        )
    )
    # Subito dopo c'è la versione con la foto nuova e l'intervento in corso.
    in_corso = _post(api, prima, scelto["post_id"])
    assert in_corso["versione_corrente"]["tipo_intervento"] == "cambio_foto"
    assert in_corso["intervento_in_corso"] == "rigenera_totale"
    assert _esegui_rigenerazioni(coda, visti) == [RIGENERA_POST]
    rifatto = _post(api, prima, scelto["post_id"])
    assert rifatto["versione_corrente"]["tipo_intervento"] == "rigenera_totale"
    assert _foto_del_post(rifatto) == [libera]
    assert rifatto["versione_corrente"]["testo"] != testo_prima
    assert rifatto["intervento_in_corso"] is None
    assert rifatto["stato"] == "da_approvare"
    # La foto vecchia non è persa e la foto del post non è due volte sul canale.
    assert vecchia not in _foto_del_post(rifatto)
    assert (
        len(
            {
                f
                for uno in _post_per_canale(_vedi(api, prima))["instagram"]
                for f in _foto_del_post(uno)
            }
        )
        == 3
    )

    # 3. Rigenera immagine su un post con immagine AI della seconda.
    ai = [
        uno
        for per_canale in _post_per_canale(_vedi(api, seconda)).values()
        for uno in per_canale
        if uno["riempitivo"] == "immagine_ai"
    ]
    assert ai, "con una sola foto per sei post ci sono immagini AI"
    scelto_ai = ai[0]
    immagine_prima = _foto_del_post(scelto_ai)
    assert "rigenera_immagine" in scelto_ai["interventi"]
    _ok(
        api(
            "POST",
            f"/post/{scelto_ai['post_id']}/rigenera-immagine",
            json={"nota": "Più luce, dall'alto."},
        )
    )
    assert _esegui_rigenerazioni(coda, visti) == [RIGENERA_IMMAGINE]
    nuovo = _post(api, seconda, scelto_ai["post_id"])
    assert nuovo["versione_corrente"]["tipo_intervento"] == "rigenera_immagine"
    assert nuovo["riempitivo"] == "immagine_ai"
    assert _foto_del_post(nuovo) != immagine_prima
    assert nuovo["versione_corrente"]["testo"].endswith("Immagine creata con AI")

    # 4. Approva le due campagne.
    assert _ok(api("POST", f"/campagne/{prima}/approva")) == {"stato": "attiva"}
    assert _ok(api("POST", f"/campagne/{seconda}/approva")) == {"stato": "attiva"}

    # 5. Lo storico dell'AI ha le chiamate di tutte e due le campagne e un voto.
    storico = _ok(api("GET", "/storico-ai"))
    assert {riga["campagna_id"] for riga in storico["voci"]} == {prima, seconda}
    tipi_prima = {
        riga["tipo"]
        for riga in _ok(api("GET", "/storico-ai", params={"campagna_id": prima}))[
            "voci"
        ]
    }
    tipi_seconda = {
        riga["tipo"]
        for riga in _ok(api("GET", "/storico-ai", params={"campagna_id": seconda}))[
            "voci"
        ]
    }
    assert {"analisi", "piano", "testo"} <= tipi_prima  # il testo riscritto compreso
    assert {"analisi", "piano", "testo", "immagine"} <= tipi_seconda
    assert all(riga["versione_prompt"] for riga in storico["voci"])

    immagine = next(
        riga
        for riga in _ok(
            api(
                "GET",
                "/storico-ai",
                params={"campagna_id": seconda, "tipo": "immagine"},
            )
        )["voci"]
        if riga["post_id"] == scelto_ai["post_id"]
    )
    voto = _ok(
        api(
            "POST",
            f"/storico-ai/{immagine['id']}/voto",
            json={"voto": 4, "nota": "Bella, ma l'inquadratura è la solita."},
        )
    )
    assert voto["voto"] == 4
    dettaglio = _ok(api("GET", f"/storico-ai/{immagine['id']}"))
    assert [(v["voto"], v["nota"]) for v in dettaglio["valutazioni"]] == [
        (4, "Bella, ma l'inquadratura è la solita.")
    ]
    numeri = _ok(api("GET", "/storico-ai/numeri", params={"campagna_id": seconda}))
    assert numeri["voto_medio"] == 4
    assert numeri["immagini_rigenerate"] >= 1
    # I numeri per versione del prompt servono a confrontare v2 e v3.
    assert {v["tipo"] for v in numeri["per_versione"]} >= {"analisi", "piano", "testo"}

    # La prima campagna: il testo riscritto è una rigenerazione contata.
    numeri_prima = _ok(api("GET", "/storico-ai/numeri", params={"campagna_id": prima}))
    assert numeri_prima["rigenerazioni_testo"] == 1
    assert numeri_prima["voto_medio"] is None

    assert isinstance(finti.ai, AIFinto)  # nessuna chiamata reale
