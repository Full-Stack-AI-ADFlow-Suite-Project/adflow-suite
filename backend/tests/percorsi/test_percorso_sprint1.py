"""T1-07: il percorso completo dello sprint 1, dal seed alla campagna conclusa.

Tutto passa dalle API, come nel percorso a mano di converge §3: il login vero
degli utenti del seed, la bozza con le foto, l'invio, il job di generazione
preso dalla coda, la revisione dell'operatore e il tick di pubblicazione.
AI, social e archivio sono quelli finti.
"""

from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image
from sqlalchemy import select, text

from app import cli, worker
from app.adapters.ai import AIFinto, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.adapters.social import SocialFinto, usa_social
from app.core import limite_login
from app.core.coda import GENERA_CAMPAGNA
from app.core.config import leggi_impostazioni
from app.core.orologio import adesso
from app.main import app
from app.moduli.artigiani.models import AccountSocial
from app.moduli.contenuti import generazione, jobs

PASSWORD = "PasswordDelSeed!2026"
ARTIGIANO, OPERATORE, ADMIN = (email for email, _, _ in cli.UTENTI_SEED)
BOTTEGA = cli.PROFILO_SEED["nome"]
DUE_CANALI = ["facebook", "instagram"]

OGGI = datetime(2030, 1, 7, 9, tzinfo=timezone.utc)  # un lunedì mattina
INIZIO = date(2030, 1, 11)  # tra 4 giorni
UNA_SETTIMANA = INIZIO + timedelta(days=6)  # 3 post a settimana: 3 post chiesti
QUATTRO_SETTIMANE = INIZIO + timedelta(days=27)  # 12 post chiesti


class Orologio:
    """L'ora di API, job e tick: il test la sposta in avanti."""

    def __init__(self, ora: datetime) -> None:
        self.ora = ora

    def __call__(self) -> datetime:
        return self.ora

    def dopo(self, giorno: date) -> None:
        """Il mattino dopo ``giorno``: ogni post fino a quel giorno è dovuto."""
        self.ora = datetime.combine(
            giorno + timedelta(days=1), OGGI.timetz(), tzinfo=timezone.utc
        )


@pytest.fixture(autouse=True)
def finti() -> Iterator[SimpleNamespace]:
    ai, social, archivio = AIFinto(), SocialFinto(), ArchivioFinto()
    with usa_ai(ai), usa_social(social), usa_archivio(archivio):
        yield SimpleNamespace(ai=ai, social=social, archivio=archivio)


@pytest.fixture(autouse=True)
def orologio(db, client, monkeypatch) -> Orologio:
    """Un'ora sola per API, job e tick, che lavorano sulla sessione del test.

    Come nel worker: commit alla fine di ogni passo, rollback se c'è un errore.
    """
    ora = Orologio(OGGI)

    @contextmanager
    def transazione():
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise

    app.dependency_overrides[adesso] = ora
    for modulo in (jobs, worker):
        monkeypatch.setattr(modulo, "transazione", transazione)
        monkeypatch.setattr(modulo, "adesso", ora)
    return ora


@pytest.fixture(autouse=True)
def accessi(db, motore_test, monkeypatch) -> Iterator[None]:
    """Il seed e il limite dei tentativi di login, sul database di test."""
    monkeypatch.setattr(limite_login, "motore", lambda: motore_test)
    monkeypatch.setattr(leggi_impostazioni(), "login_limite_tentativi", 1000)
    cli.esegui_seed(db, PASSWORD)
    db.commit()
    yield
    # i contatori del limite si scrivono fuori dalla transazione del test
    with motore_test.begin() as connessione:
        connessione.execute(text("DELETE FROM limite_login"))


@pytest.fixture
def api(db, client) -> Callable:
    """Una richiesta come nell'API vera: commit se riesce, rollback se no."""

    def richiesta(metodo: str, percorso: str, **argomenti):
        risposta = client.request(metodo, f"/api{percorso}", **argomenti)
        if risposta.status_code < 400:
            db.commit()
        else:
            db.rollback()
        return risposta

    return richiesta


@pytest.fixture
def entra(api, client) -> Callable:
    def login(email: str) -> dict:
        client.cookies.clear()
        risposta = api(
            "POST", "/auth/login", json={"email": email, "password": PASSWORD}
        )
        assert risposta.status_code == 200, risposta.text
        return risposta.json()

    return login


@pytest.fixture
def lavora(coda) -> Callable:
    """Esegue i job di generazione in coda come Procrastinate.

    Restituisce quante esecuzioni ha chiesto ogni job (al massimo 3).
    """
    fatti: set[int] = set()

    def esegui() -> list[int]:
        esecuzioni = []
        for id_job, job in list(coda.jobs.items()):
            if id_job in fatti or job["task_name"] != GENERA_CAMPAGNA:
                continue
            fatti.add(id_job)
            for esecuzione in range(1, generazione.ESECUZIONI + 1):
                if not jobs.esegui_generazione(job["args"]["campagna_id"], esecuzione):
                    break
            else:
                raise AssertionError(
                    "Alla terza esecuzione il job chiede di ripartire."
                )
            esecuzioni.append(esecuzione)
        return esecuzioni

    return esegui


def _foto_jpeg(tinta: int) -> bytes:
    """Una foto vera di 1080 × 1350 px, diversa a ogni tinta."""
    uscita = BytesIO()
    Image.new("RGB", (1080, 1350), (tinta, 120, 90)).save(uscita, "JPEG")
    return uscita.getvalue()


def _carica(api, campagna_id: int, gruppo_id: int, contenuto: bytes, nome="foto.jpg"):
    return api(
        "POST",
        f"/campagne/{campagna_id}/foto",
        files={"file": (nome, contenuto, "image/jpeg")},
        data={"gruppo_id": str(gruppo_id)},
    )


def _bozza(api, fine: date, *, foto_per_gruppo: tuple[int, ...]) -> tuple[int, list]:
    """Bozza sui due canali con i suoi gruppi di foto: id della campagna e delle foto."""
    risposta = api(
        "POST",
        "/campagne",
        json={
            "titolo": "Novità di gennaio",
            "inizio": INIZIO.isoformat(),
            "fine": fine.isoformat(),
            "descrizione": "I pezzi appena usciti dal forno.",
            "canali": DUE_CANALI,
        },
    )
    assert risposta.status_code == 201, risposta.text
    campagna_id = risposta.json()["id"]
    foto = []
    for numero, quante in enumerate(foto_per_gruppo, start=1):
        gruppo = api(
            "POST",
            f"/campagne/{campagna_id}/gruppi",
            json={"descrizione": f"Servizio di piatti numero {numero}"},
        )
        assert gruppo.status_code == 201, gruppo.text
        for _ in range(quante):
            caricata = _carica(
                api, campagna_id, gruppo.json()["id"], _foto_jpeg(40 * len(foto))
            )
            assert caricata.status_code == 201, caricata.text
            foto.append(caricata.json()["id"])
    return campagna_id, foto


def _stato(api, campagna_id: int) -> str:
    return api("GET", f"/campagne/{campagna_id}").json()["stato"]


def _vedi(api, campagna_id: int) -> dict:
    risposta = api("GET", f"/campagne/{campagna_id}/post")
    assert risposta.status_code == 200, risposta.text
    return risposta.json()


def _post_per_canale(vista: dict) -> dict[str, list[dict]]:
    per_canale = defaultdict(list)
    for uscita in vista["uscite"]:
        for post in uscita["post"]:
            per_canale[post["canale"]].append(post)
    return per_canale


def _foto_del_post(post: dict) -> list[int]:
    return [foto["foto_id"] for foto in post["versione_corrente"]["foto"]]


def _account(db, piattaforma: str) -> AccountSocial:
    return db.scalar(
        select(AccountSocial).where(AccountSocial.piattaforma == piattaforma)
    )


def test_percorso_dalla_bozza_alla_campagna_conclusa(
    api, entra, lavora, orologio, finti, coda
):
    """Converge §3, passi 1–5: 7 giorni, 2 canali, 4 foto in 2 gruppi, una stella."""
    assert entra(ARTIGIANO)["ruolo"] == "artigiano"
    assert api("GET", "/canali").json() == [
        {"canale": canale, "collegato": True} for canale in DUE_CANALI
    ]

    campagna_id, foto = _bozza(api, UNA_SETTIMANA, foto_per_gruppo=(2, 2))
    stella = foto[-1]
    assert api("PUT", f"/foto/{stella}", json={"da_usare": True}).status_code == 200
    bozza = api("GET", f"/campagne/{campagna_id}").json()
    assert bozza["stato"] == "bozza"
    assert bozza["post_chiesti_per_canale"] == {"facebook": 3, "instagram": 3}
    assert bozza["avvisi"] == []

    inviata = api("POST", f"/campagne/{campagna_id}/invia")
    assert (inviata.status_code, inviata.json()["stato"]) == (200, "inviata")
    assert [job["task_name"] for job in coda.jobs.values()] == [GENERA_CAMPAGNA]

    assert lavora() == [1]
    assert _stato(api, campagna_id) == "in_revisione"

    assert entra(OPERATORE)["ruolo"] == "operatore"
    [riga] = api("GET", "/campagne", params={"stato": "in_revisione"}).json()
    assert (riga["id"], riga["bottega"], riga["citta"]) == (
        campagna_id,
        BOTTEGA,
        cli.PROFILO_SEED["citta"],
    )
    # La fotografia del profilo ha i nomi delle colonne del profilo (R-11).
    dettaglio = api("GET", f"/campagne/{campagna_id}").json()
    assert dettaglio["profilo_snapshot"]["nome"] == BOTTEGA
    assert dettaglio["profilo_snapshot"]["vincoli"] == cli.PROFILO_SEED["vincoli"]

    vista = _vedi(api, campagna_id)
    assert vista["piano"]["debole"] is False
    assert [uscita["numero"] for uscita in vista["uscite"]] == [1, 2, 3]
    per_canale = _post_per_canale(vista)
    assert sorted(per_canale) == DUE_CANALI
    for post in per_canale.values():
        assert len(post) == 3  # quelli chiesti (R-05)
        assert all(uno["stato"] == "da_approvare" for uno in post)
        assert not any(uno["da_rivedere"] for uno in post)
        assert all(uno["riempitivo"] is None for uno in post)
        usate = [foto_id for uno in post for foto_id in _foto_del_post(uno)]
        assert len(usate) == len(set(usate)) == 3  # mai due volte sul canale
        assert stella in usate
        assert set(usate) <= set(foto)

    assert api("POST", f"/campagne/{campagna_id}/approva").json() == {"stato": "attiva"}
    worker.tick_pubblicazione(0)
    assert finti.social.pubblicazioni == []  # nessun post è ancora dovuto

    orologio.dopo(UNA_SETTIMANA)
    worker.tick_pubblicazione(0)
    worker.tick_pubblicazione(0)
    assert len(finti.social.pubblicazioni) == 6  # una volta sola per post
    assert all(uscito["n_foto"] == 1 for uscito in finti.social.pubblicazioni)

    entra(OPERATORE)  # la sessione di prima è scaduta
    vista = _vedi(api, campagna_id)
    assert vista["campagna"]["stato"] == "conclusa"
    assert {post["stato"] for uscita in vista["uscite"] for post in uscita["post"]} == {
        "pubblicato"
    }

    entra(ARTIGIANO)
    assert [riga["stato"] for riga in api("GET", "/campagne").json()] == ["conclusa"]


def test_percorso_del_piano_debole_con_le_cartoline(
    api, entra, lavora, orologio, finti
):
    """Converge §3, passo 7: 4 settimane con 4 foto, Prosegui, 8 cartoline (R-28)."""
    entra(ARTIGIANO)
    campagna_id, foto = _bozza(api, QUATTRO_SETTIMANE, foto_per_gruppo=(4,))
    bozza = api("GET", f"/campagne/{campagna_id}").json()
    assert bozza["post_chiesti_per_canale"] == {"facebook": 12, "instagram": 12}
    assert {"foto_poche", "riempitivi_molti"} <= set(bozza["avvisi"])

    assert api("POST", f"/campagne/{campagna_id}/invia").status_code == 200
    assert lavora() == [1]
    assert _stato(api, campagna_id) == "piano_da_rivedere"

    entra(OPERATORE)
    assert _vedi(api, campagna_id)["piano"]["debole"] is True
    assert api("POST", f"/campagne/{campagna_id}/prosegui").json() == {
        "stato": "in_generazione"
    }
    assert lavora() == [1]

    vista = _vedi(api, campagna_id)
    assert vista["campagna"]["stato"] == "in_revisione"
    for post in _post_per_canale(vista).values():
        assert len(post) == 12
        con_foto = [uno for uno in post if uno["riempitivo"] is None]
        cartoline = [uno for uno in post if uno["riempitivo"] == "cartolina"]
        assert (len(con_foto), len(cartoline)) == (4, 8)
        assert {foto_id for uno in con_foto for foto_id in _foto_del_post(uno)} == set(
            foto
        )
        # ogni cartolina ha la sua immagine e il suo testo
        immagini = [foto_id for uno in cartoline for foto_id in _foto_del_post(uno)]
        assert len(immagini) == len(set(immagini)) == 8
        assert all(uno["versione_corrente"]["testo"] for uno in cartoline)

    assert api("POST", f"/campagne/{campagna_id}/approva").status_code == 200
    orologio.dopo(QUATTRO_SETTIMANE)
    worker.tick_pubblicazione(0)
    assert len(finti.social.pubblicazioni) == 24
    entra(OPERATORE)
    assert _stato(api, campagna_id) == "conclusa"


def test_percorso_della_riprova_dopo_tre_esecuzioni_fallite(api, entra, lavora, finti):
    """CA-19 dall'inizio alla fine: fallita, l'errore accanto a Riprova, riparte."""
    entra(ARTIGIANO)
    campagna_id, _ = _bozza(api, UNA_SETTIMANA, foto_per_gruppo=(2, 2))
    finti.ai.comanda_errore("pianifica_campagna", "temporaneo", volte=None)
    assert api("POST", f"/campagne/{campagna_id}/invia").status_code == 200

    assert lavora() == [3]
    assert _stato(api, campagna_id) == "generazione_fallita"
    assert api("POST", f"/campagne/{campagna_id}/riprova").status_code == 403

    entra(OPERATORE)
    errore = _vedi(api, campagna_id)["ultimo_errore"]
    assert (errore["tipo"], errore["tappa"]) == ("temporaneo", "piano")
    assert errore["messaggio"]

    riprova = api("POST", f"/campagne/{campagna_id}/riprova")
    assert (riprova.status_code, riprova.json()["stato"]) == (200, "inviata")
    with usa_ai(AIFinto()) as riparata:
        assert lavora() == [1]
    # le foto già analizzate non si rianalizzano (CA-50)
    assert "analizza_gruppo" not in {c["operazione"] for c in riparata.chiamate}
    vista = _vedi(api, campagna_id)
    assert vista["campagna"]["stato"] == "in_revisione"
    assert all(len(post) == 3 for post in _post_per_canale(vista).values())


def test_prove_negative_del_percorso(api, entra, lavora, db, finti):
    """Converge §3, passo 6: ogni rifiuto ha il suo codice e un messaggio in italiano."""
    entra(ARTIGIANO)

    def crea(inizio: date, fine: date):
        return api(
            "POST",
            "/campagne",
            json={
                "titolo": "Prova",
                "inizio": inizio.isoformat(),
                "fine": fine.isoformat(),
                "canali": DUE_CANALI,
            },
        )

    def rifiutata(risposta, codice: int) -> None:
        assert risposta.status_code == codice, risposta.text
        assert isinstance(risposta.json()["detail"], str)

    domani = OGGI.date() + timedelta(days=1)
    rifiutata(crea(domani, domani + timedelta(days=6)), 422)  # inizio tra 1 giorno
    rifiutata(crea(INIZIO, INIZIO + timedelta(days=2)), 422)  # durata di 3 giorni
    _account(db, "instagram").stato = "scollegato"
    db.commit()
    rifiutata(crea(INIZIO, UNA_SETTIMANA), 422)  # canale non collegato
    _account(db, "instagram").stato = "collegato"
    db.commit()

    campagna_id, _ = _bozza(api, UNA_SETTIMANA, foto_per_gruppo=(3,))
    gruppo_id = api("GET", f"/campagne/{campagna_id}").json()["gruppi"][0]["id"]
    pdf = _carica(api, campagna_id, gruppo_id, b"%PDF-1.4\n%finto\n", nome="foto.pdf")
    rifiutata(pdf, 422)  # un PDF come foto
    rifiutata(api("POST", f"/campagne/{campagna_id}/invia"), 422)  # con 3 foto

    # l'artigiano non entra nelle funzioni dell'operatore, l'admin sì
    rifiutata(api("POST", f"/campagne/{campagna_id}/approva"), 403)
    entra(ADMIN)
    rifiutata(api("POST", f"/campagne/{campagna_id}/approva"), 409)

    entra(ARTIGIANO)
    assert _carica(api, campagna_id, gruppo_id, _foto_jpeg(200)).status_code == 201
    _account(db, "instagram").stato = "scollegato"
    db.commit()
    rifiutata(api("POST", f"/campagne/{campagna_id}/invia"), 409)  # scollegato dopo
    _account(db, "instagram").stato = "collegato"
    db.commit()

    # errore di configurazione dell'AI: fallita subito, senza altre esecuzioni
    finti.ai.comanda_errore("analizza_gruppo", "configurazione", volte=None)
    assert api("POST", f"/campagne/{campagna_id}/invia").status_code == 200
    assert lavora() == [1]
    entra(OPERATORE)
    vista = _vedi(api, campagna_id)
    assert vista["campagna"]["stato"] == "generazione_fallita"
    assert (vista["ultimo_errore"]["tipo"], vista["ultimo_errore"]["tappa"]) == (
        "configurazione",
        "analisi",
    )
