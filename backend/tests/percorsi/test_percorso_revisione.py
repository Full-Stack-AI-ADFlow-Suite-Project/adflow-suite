"""Percorso completo di revisione, notifiche e scadenze attraverso le API.

Verifica la revisione, le notifiche e le
scadenze, tutto attraverso le API con AI, social, archivio ed email finti:

1. campagna A a `in_revisione`: notifica `campagna_pronta` una per operatore,
   l'artigiano non vede piano né post (CA-31, CA-55);
2. Vedi campagna: nota interna (CA-23, CA-69), modifica a mano (CA-64), spunta
   (CA-65), rigenera totale e da proposta (CA-26…CA-28), approva bloccata
   mentre l'intervento è in corso (CA-66);
3. togli il canale con nota, ultimo canale → 409, approva (CA-53);
4. campagna B respinta con motivo, nota e 2 foto segnate: email all'artigiano
   con motivo, nota e 2 miniature (CA-24, CA-25, CA-31);
5. campagna C: sospendi → il tick non pubblica; riattiva con un arretrato;
   annulla; interventi vietati in attiva e sospesa (CA-29, CA-32);
6. campagna D: post `fallito` → notifica `post_fallito`; riprogramma dentro e
   fuori periodo, su un post non fallito (CA-55, CA-67);
7. scadenze col tick: post `scaduto`, campagna `scaduta` con email, campagna
   ferma → `generazione_fallita` con errore `temporaneo` (CA-30, CA-55, CA-68);
8. prove negative: interventi di un artigiano → 403, nota/respingi su bozza o
   su stati sbagliati → rifiutati.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image
from sqlalchemy import func, select, text

from app import cli, worker
from app.adapters.ai import AIFinto, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.adapters.email import EmailFinto, usa_email
from app.adapters.social import SocialFinto, usa_social
from app.core import limite_login
from app.core.coda import GENERA_CAMPAGNA, INVIA_NOTIFICA, RIGENERA_POST
from app.core.config import leggi_impostazioni
from app.core.orologio import adesso
from app.main import app
from app.moduli.accesso import service as accesso_service
from app.moduli.campagne.models import DecisioneCampagna, Foto
from app.moduli.contenuti import generazione
from app.moduli.contenuti import jobs as jobs_contenuti
from app.moduli.contenuti.models import Post
from app.moduli.notifiche import jobs as jobs_notifiche
from app.moduli.notifiche.models import Notifica

PASSWORD = "PasswordDelSeed!2026"
ARTIGIANO, OPERATORE, ADMIN = (email for email, _, _ in cli.UTENTI_SEED)
DUE_CANALI = ["facebook", "instagram"]

OGGI = datetime(2030, 6, 1, 9, tzinfo=timezone.utc)  # un lunedì mattina
INIZIO = date(2030, 6, 5)  # tra 4 giorni
UNA_SETTIMANA = INIZIO + timedelta(days=6)


class Orologio:
    """L'ora di API, job e tick: il test la sposta in avanti."""

    def __init__(self, ora: datetime) -> None:
        self.ora = ora

    def __call__(self) -> datetime:
        return self.ora

    def avanti(self, delta: timedelta) -> None:
        self.ora = self.ora + delta


@pytest.fixture(autouse=True)
def finti() -> Iterator[SimpleNamespace]:
    ai, social, archivio, email = (
        AIFinto(),
        SocialFinto(),
        ArchivioFinto(),
        EmailFinto(),
    )
    with usa_ai(ai), usa_social(social), usa_archivio(archivio), usa_email(email):
        yield SimpleNamespace(ai=ai, social=social, archivio=archivio, email=email)


@pytest.fixture(autouse=True)
def orologio(db, client, monkeypatch) -> Orologio:
    """Un'ora sola per API, job e tick, che lavorano sulla sessione del test."""
    ora = Orologio(OGGI)

    @contextmanager
    def transazione():
        with db.begin_nested():
            yield db

    app.dependency_overrides[adesso] = ora
    for modulo in (jobs_contenuti, jobs_notifiche, worker):
        monkeypatch.setattr(modulo, "transazione", transazione)
        monkeypatch.setattr(modulo, "adesso", ora)
    return ora


@pytest.fixture(autouse=True)
def accessi(db, motore_test, monkeypatch) -> Iterator[None]:
    """Il seed e il limite dei tentativi di login, sul database di test."""
    monkeypatch.setattr(limite_login, "motore", lambda: motore_test)
    monkeypatch.setattr(leggi_impostazioni(), "login_limite_tentativi", 1000)
    cli.esegui_seed(db, PASSWORD)
    accesso_service.crea_utente(
        db,
        email="operatore2@example.com",
        nome="Secondo Operatore",
        ruolo="operatore",
        password=PASSWORD,
    )
    db.commit()
    yield
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
    """Esegue i job accodati come farebbe il worker Procrastinate."""
    fatti: set[int] = set()

    def esegui() -> list[int]:
        eseguiti = []
        for id_job, job in list(coda.jobs.items()):
            if id_job in fatti:
                continue
            if job["task_name"] == GENERA_CAMPAGNA:
                for esecuzione in range(1, generazione.ESECUZIONI + 1):
                    if not jobs_contenuti.esegui_generazione(
                        job["args"]["campagna_id"], esecuzione
                    ):
                        break
            elif job["task_name"] == RIGENERA_POST:
                args = job["args"]
                for esecuzione in range(1, generazione.ESECUZIONI + 1):
                    if not jobs_contenuti.esegui_rigenerazione(
                        args["post_id"],
                        args.get("testo_proposto"),
                        args.get("nota"),
                        esecuzione,
                    ):
                        break
            elif job["task_name"] == INVIA_NOTIFICA:
                args = job["args"]
                for tentativo in range(1, jobs_notifiche.TENTATIVI + 1):
                    if not jobs_notifiche.esegui_invio(
                        args["notifica_id"], args.get("contenuto"), tentativo
                    ):
                        break
            else:
                continue
            fatti.add(id_job)
            eseguiti.append(id_job)
        return eseguiti

    return esegui


def _foto_jpeg(tinta: int, larghezza: int = 1080, altezza: int = 1350) -> bytes:
    uscita = BytesIO()
    Image.new("RGB", (larghezza, altezza), (tinta % 255, 120, 90)).save(uscita, "JPEG")
    return uscita.getvalue()


def _nuova_campagna(
    api, entra, lavora, titolo: str, inizio: date, fine: date, n_foto: int = 4
) -> tuple[int, list[int]]:
    """Bozza con foto, invio e generazione: resta in ``in_revisione``."""
    assert entra(ARTIGIANO)["ruolo"] == "artigiano"
    campagna_id = api(
        "POST",
        "/campagne",
        json={
            "titolo": titolo,
            "inizio": inizio.isoformat(),
            "fine": fine.isoformat(),
            "canali": DUE_CANALI,
        },
    ).json()["id"]
    gruppo = api(
        "POST",
        f"/campagne/{campagna_id}/gruppi",
        json={"descrizione": "Foto della bottega"},
    ).json()["id"]
    foto_ids = []
    for i in range(n_foto):
        risposta = api(
            "POST",
            f"/campagne/{campagna_id}/foto",
            files={"file": (f"f{i}.jpg", _foto_jpeg(10 + 20 * i), "image/jpeg")},
            data={"gruppo_id": str(gruppo)},
        )
        assert risposta.status_code == 201, risposta.text
        foto_ids.append(risposta.json()["id"])
    assert (
        api(
            "POST",
            f"/campagne/{campagna_id}/invia",
            json={"dichiarazione": True},
        ).status_code
        == 200
    )
    assert lavora()
    return campagna_id, foto_ids


def _stato(api, campagna_id: int) -> str:
    return api("GET", f"/campagne/{campagna_id}").json()["stato"]


def _vedi(api, campagna_id: int) -> dict:
    risposta = api("GET", f"/campagne/{campagna_id}/post")
    assert risposta.status_code == 200, risposta.text
    return risposta.json()


def _post_piano(vista: dict) -> list[dict]:
    """I post del piano, nell'ordine delle uscite."""
    return [post for uscita in vista["uscite"] for post in uscita["post"]]


def _tick() -> None:
    """Il minuto del worker: scadenze, poi pubblicazione."""
    worker.tick_pubblicazione(0)


def _notifiche(db, *, tipo=None, campagna_id=None):
    elenco = db.scalars(select(Notifica)).all()
    return [
        n
        for n in elenco
        if (tipo is None or n.tipo == tipo)
        and (campagna_id is None or n.campagna_id == campagna_id)
    ]


def _decisioni(db, campagna_id: int) -> list[DecisioneCampagna]:
    return list(
        db.scalars(
            select(DecisioneCampagna)
            .where(DecisioneCampagna.campagna_id == campagna_id)
            .order_by(DecisioneCampagna.id)
        )
    )


def test_percorso_completo_revisione(
    api, client, entra, lavora, orologio, finti, db, coda
):
    """Test completo del percorso di revisione, notifiche e scadenze."""

    # =========================================================================
    # 1. Campagna A a in_revisione: notifiche e vista artigiano (CA-31, CA-55)
    # =========================================================================
    a_id, _ = _nuova_campagna(api, entra, lavora, "Campagna A", INIZIO, UNA_SETTIMANA)
    assert _stato(api, a_id) == "in_revisione"

    # Una notifica campagna_pronta per ogni operatore/admin attivo: 3.
    pronte = _notifiche(db, tipo="campagna_pronta", campagna_id=a_id)
    assert len(pronte) == 3
    lavora()
    assert len(finti.email.inviate) == 3
    assert all("Campagna A" in e.oggetto for e in finti.email.inviate)

    # Rieseguire il job non rimanda l'email (stato già `inviata`).
    n_prima = len(finti.email.inviate)
    for n in pronte:
        jobs_notifiche.esegui_invio(n.id, None, 1)
    assert len(finti.email.inviate) == n_prima
    assert all(n.stato_invio == "inviata" for n in pronte)

    # L'artigiano vede la campagna ma nessun piano e nessun post (CA-31).
    dettaglio = api("GET", f"/campagne/{a_id}").json()
    assert dettaglio["stato"] == "in_revisione"
    assert "post" not in dettaglio and "uscite" not in dettaglio
    assert dettaglio["decisioni"] == []
    assert dettaglio["profilo_snapshot"] is None

    # =========================================================================
    # 2. Vedi campagna: nota, modifica, spunta, rigenera, approva (CA-23…CA-28,
    #    CA-64, CA-65, CA-66, CA-69)
    # =========================================================================
    assert entra(OPERATORE)["ruolo"] == "operatore"
    vista = _vedi(api, a_id)
    post_a = _post_piano(vista)
    assert len(post_a) >= 4  # 3 per canale in 7 giorni, su 2 canali
    [post_primo, post_altro] = [p for p in post_a if p["stato"] == "da_approvare"][:2]

    # Nota interna: stato invariato, nessuna email, visibile in da-approvare.
    n_email = len(finti.email.inviate)
    n_notifiche = db.scalar(select(func.count(Notifica.id)))
    assert (
        api(
            "POST", f"/campagne/{a_id}/nota", json={"nota": "Guardare il piano."}
        ).status_code
        == 200
    )
    assert _stato(api, a_id) == "in_revisione"
    assert len(finti.email.inviate) == n_email
    assert db.scalar(select(func.count(Notifica.id))) == n_notifiche
    riga = next(c for c in api("GET", "/da-approvare").json() if c["id"] == a_id)
    assert riga["ultima_nota"] == "Guardare il piano."

    # L'artigiano non vede la nota interna (R-32).
    assert entra(ARTIGIANO)
    dettaglio = api("GET", f"/campagne/{a_id}").json()
    assert all("Guardare" not in (d.get("nota") or "") for d in dettaglio["decisioni"])
    assert entra(OPERATORE)

    # Modifica a mano: versione modifica_operatore, spunta azzerata (CA-64).
    versione_prima = post_primo["versione_corrente"]
    assert (
        api(
            "POST",
            f"/post/{post_primo['post_id']}/modifica",
            json={
                "testo": versione_prima["testo"],
                "hashtag": versione_prima["hashtag"],
            },
        ).status_code
        == 422  # uguale a prima
    )
    assert (
        api(
            "POST",
            f"/post/{post_primo['post_id']}/modifica",
            json={"testo": "Testo riscritto dall'operatore."},
        ).status_code
        == 200
    )
    vista = _vedi(api, a_id)
    post_modificato = next(
        p for p in _post_piano(vista) if p["post_id"] == post_primo["post_id"]
    )
    assert post_modificato["versione_corrente"]["autore_id"] is not None
    assert post_modificato["controllato_da"] is None

    # Spunta "va bene": chi e quando; su un post da_rivedere → rifiutata.
    assert (
        api(
            "POST",
            f"/post/{post_primo['post_id']}/controllato",
            json={"valore": True},
        ).status_code
        == 200
    )
    post_spuntato = next(
        p
        for p in _post_piano(_vedi(api, a_id))
        if p["post_id"] == post_primo["post_id"]
    )
    assert post_spuntato["controllato_da"] is not None
    assert post_spuntato["controllato_il"] is not None

    da_rivedere = next((p for p in _post_piano(vista) if p["da_rivedere"]), None)
    if da_rivedere is not None:
        assert (
            api(
                "POST",
                f"/post/{da_rivedere['post_id']}/controllato",
                json={"valore": True},
            ).status_code
            == 409
        )

    # Rigenera da proposta senza testo → 422; poi totale e da proposta.
    assert (
        api(
            "POST",
            f"/post/{post_altro['post_id']}/rigenera",
            json={"modalita": "da_proposta"},
        ).status_code
        == 422
    )
    assert (
        api(
            "POST",
            f"/post/{post_altro['post_id']}/rigenera",
            json={"modalita": "totale"},
        ).status_code
        == 200
    )
    # Finché l'intervento è in corso l'approvazione è bloccata (CA-66).
    assert api("POST", f"/campagne/{a_id}/approva").status_code == 409
    lavora()  # esegue il job rigenera_post
    post_rigen = next(
        p
        for p in _post_piano(_vedi(api, a_id))
        if p["post_id"] == post_altro["post_id"]
    )
    assert post_rigen["intervento_in_corso"] is None
    assert post_rigen["controllato_da"] is None  # nuova versione, spunta azzerata

    assert (
        api(
            "POST",
            f"/post/{post_altro['post_id']}/rigenera",
            json={
                "modalita": "da_proposta",
                "testo_proposto": "Un testo scritto dall'operatore.",
            },
        ).status_code
        == 200
    )
    lavora()
    assert (
        api(
            "POST",
            f"/post/{post_altro['post_id']}/rigenera",
            json={"modalita": "totale"},
        ).status_code
        == 200
    )
    lavora()
    # Alla quarta → 409: la modifica a mano fatta prima resta.
    assert (
        api(
            "POST",
            f"/post/{post_altro['post_id']}/rigenera",
            json={"modalita": "totale"},
        ).status_code
        == 409
    )
    post_primo_ancora = next(
        p
        for p in _post_piano(_vedi(api, a_id))
        if p["post_id"] == post_primo["post_id"]
    )
    assert post_primo_ancora["versione_corrente"]["testo"] == (
        "Testo riscritto dall'operatore."
    )

    # =========================================================================
    # 3. Togli il canale con nota; l'ultimo → 409; approva (CA-53)
    # =========================================================================
    assert (
        api(
            "POST",
            f"/campagne/{a_id}/togli-canale",
            json={"canale": "instagram", "nota": "Instagram non è adatto."},
        ).status_code
        == 200
    )
    vista = _vedi(api, a_id)
    assert all(
        p["stato"] == "scartato"
        for p in _post_piano(vista)
        if p["canale"] == "instagram"
    )
    # Rimasto un canale solo: toglierlo è vietato (409).
    assert (
        api(
            "POST",
            f"/campagne/{a_id}/togli-canale",
            json={"canale": "facebook", "nota": "Anche questo."},
        ).status_code
        == 409
    )
    assert api("POST", f"/campagne/{a_id}/approva").status_code == 200
    assert _stato(api, a_id) == "attiva"

    # L'artigiano vede il canale tolto e la nota (CA-53).
    assert entra(ARTIGIANO)
    dettaglio = api("GET", f"/campagne/{a_id}").json()
    assert dettaglio["canali_tolti"] == ["instagram"]
    [decisione_tolto] = dettaglio["decisioni"]
    assert decisione_tolto["esito"] == "canale_tolto"
    assert decisione_tolto["nota"] == "Instagram non è adatto."

    # In attiva rigenera e spunta → rifiutate (CA-29); la modifica di un post che
    # esce tra più di 15 minuti è ammessa (CA-84), quella entro il margine no.
    assert entra(OPERATORE)
    post_attivo = _post_piano(_vedi(api, a_id))[0]
    assert (
        api(
            "POST",
            f"/post/{post_attivo['post_id']}/rigenera",
            json={"modalita": "totale"},
        ).status_code
        == 409
    )
    assert (
        api(
            "POST",
            f"/post/{post_attivo['post_id']}/controllato",
            json={"valore": True},
        ).status_code
        == 409
    )

    # =========================================================================
    # 4. Campagna B respinta: prove negative, poi motivo+nota+2 foto (CA-24,25)
    # =========================================================================
    # Periodo libero: A (attiva) occupa INIZIO–UNA_SETTIMANA. Dall'ADR-119 le
    # campagne della stessa bottega possono sovrapporsi (CA-12); qui si sceglie
    # comunque un periodo diverso per non confondere i post delle due campagne.
    b_id, foto_b = _nuova_campagna(
        api,
        entra,
        lavora,
        "Campagna B",
        INIZIO + timedelta(days=10),
        UNA_SETTIMANA + timedelta(days=10),
    )
    assert _stato(api, b_id) == "in_revisione"
    assert entra(OPERATORE)

    assert (
        api(
            "POST",
            f"/campagne/{b_id}/respingi",
            json={"nota": "Da rifare."},
        ).status_code
        == 422
    )
    assert (
        api(
            "POST",
            f"/campagne/{b_id}/respingi",
            json={"motivo": "foto"},
        ).status_code
        == 422
    )
    assert (
        api(
            "POST",
            f"/campagne/{b_id}/respingi",
            json={
                "motivo": "foto",
                "nota": "Le foto del banco sono troppo buie.",
                "foto_segnate": foto_b[:2],
            },
        ).status_code
        == 200
    )
    assert _stato(api, b_id) == "respinta"
    assert all(p["stato"] == "scartato" for p in _post_piano(_vedi(api, b_id)))

    # L'email all'artigiano ha motivo, nota e 2 miniature (CA-25).
    lavora()
    (email_respinta,) = [
        e for e in finti.email.inviate if "respinta" in e.oggetto.lower()
    ]
    assert email_respinta.destinatario == ARTIGIANO
    assert "foto da rifare" in email_respinta.corpo
    assert "Le foto del banco sono troppo buie." in email_respinta.corpo
    assert [a.nome for a in email_respinta.allegati] == [
        "miniatura-1.jpg",
        "miniatura-2.jpg",
    ]

    # L'artigiano rivede motivo, nota e foto segnate (CA-31).
    assert entra(ARTIGIANO)
    dettaglio_b = api("GET", f"/campagne/{b_id}").json()
    assert dettaglio_b["esito_respinta"]["motivo"] == "foto"
    assert dettaglio_b["esito_respinta"]["nota"] == (
        "Le foto del banco sono troppo buie."
    )
    assert dettaglio_b["esito_respinta"]["foto_segnate"] == foto_b[:2]

    # =========================================================================
    # 5. Campagna C: sospendi, riattiva con un arretrato, annulla (CA-29, CA-32)
    # =========================================================================
    c_id, _ = _nuova_campagna(
        api,
        entra,
        lavora,
        "Campagna C",
        UNA_SETTIMANA + timedelta(days=1),
        UNA_SETTIMANA + timedelta(days=7),
    )
    assert entra(OPERATORE)
    assert api("POST", f"/campagne/{c_id}/approva").status_code == 200
    assert _stato(api, c_id) == "attiva"

    # Sospendi: il tick non pubblica neanche i post dovuti di questa campagna.
    assert api("POST", f"/campagne/{c_id}/sospendi").status_code == 200
    orologio.avanti(timedelta(days=15))  # ora siamo oltre l'inizio di A e di C
    _tick()  # pubblica A fino a concluderla; C resta sospesa
    assert entra(OPERATORE)  # la sessione è scaduta con l'avanzamento
    assert _stato(api, a_id) == "conclusa"
    assert _stato(api, c_id) == "sospesa"
    assert all(
        p["stato"] == "approvato"
        for p in _post_piano(_vedi(api, c_id))
        if datetime.fromisoformat(p["data_ora"]) < orologio.ora
    )

    # Riattiva scegliendo un arretrato da far uscire adesso: gli altri arretrati
    # diventano annullati.
    arretrati = [
        p
        for p in _post_piano(_vedi(api, c_id))
        if p["stato"] == "approvato"
        and datetime.fromisoformat(p["data_ora"]) < orologio.ora
    ]
    assert arretrati
    prescelto = arretrati[0]
    n_pubblicate = len(finti.social.pubblicazioni)
    r_riattiva = api(
        "POST",
        f"/campagne/{c_id}/riattiva",
        json={"pubblica_ora": [prescelto["post_id"]]},
    )
    assert r_riattiva.status_code == 200, r_riattiva.text
    _tick()  # il prescelto esce al primo tick dopo la riattivazione
    assert len(finti.social.pubblicazioni) == n_pubblicate + 1
    stati = {p["post_id"]: p["stato"] for p in _post_piano(_vedi(api, c_id))}
    assert stati[prescelto["post_id"]] == "pubblicato"
    assert all(stati[p["post_id"]] == "annullato" for p in arretrati[1:])

    # Annulla: i post approvati diventano annullati (CA-32).
    assert api("POST", f"/campagne/{c_id}/annulla").status_code == 200
    assert _stato(api, c_id) == "annullata"
    assert all(
        p["stato"] in {"annullato", "pubblicato", "scartato"}
        for p in _post_piano(_vedi(api, c_id))
    )
    esiti_c = {d.esito for d in _decisioni(db, c_id)}
    assert {"sospesa", "riattivata", "annullata"} <= esiti_c

    # =========================================================================
    # 6. Campagna D: post fallito, notifica, riprogramma (CA-55, CA-67)
    # =========================================================================
    inizio_d = orologio.ora.date() + timedelta(days=3)
    d_id, _ = _nuova_campagna(
        api, entra, lavora, "Campagna D", inizio_d, inizio_d + timedelta(days=6)
    )
    assert entra(OPERATORE)
    assert api("POST", f"/campagne/{d_id}/approva").status_code == 200
    vista_d = _vedi(api, d_id)
    post_d = _post_piano(vista_d)[0]
    riga_post = db.get(Post, post_d["post_id"])
    riga_post.data_ora = orologio.ora - timedelta(hours=1)
    riga_post.versione_corrente.testo = "Testo con FAIL_DEF"
    db.commit()
    _tick()
    post_fallito = next(
        p for p in _post_piano(_vedi(api, d_id)) if p["post_id"] == post_d["post_id"]
    )
    assert post_fallito["stato"] == "fallito"
    # La notifica post_fallito va agli operatori (CA-55).
    fallite = _notifiche(db, tipo="post_fallito", campagna_id=d_id)
    assert len(fallite) == 3
    lavora()
    assert any("non pubblicato" in e.oggetto.lower() for e in finti.email.inviate)

    # Riprogramma: dentro il periodo → approvato + decisione; fuori → 422;
    # su un post non fallito → 409 (CA-67).
    assert (
        api(
            "POST",
            f"/post/{post_d['post_id']}/riprogramma",
            json={"data_ora": (orologio.ora - timedelta(days=1)).isoformat()},
        ).status_code
        == 422  # la nuova data è nel passato rispetto all'orologio
    )
    nuova_data = datetime(
        inizio_d.year, inizio_d.month, inizio_d.day, 10, tzinfo=timezone.utc
    ) + timedelta(days=1)
    assert (
        api(
            "POST",
            f"/post/{post_d['post_id']}/riprogramma",
            json={"data_ora": nuova_data.isoformat()},
        ).status_code
        == 200
    )
    post_ripro = next(
        p for p in _post_piano(_vedi(api, d_id)) if p["post_id"] == post_d["post_id"]
    )
    assert post_ripro["stato"] == "approvato"
    assert any(d.esito == "riprogrammato" for d in _decisioni(db, d_id))
    assert (
        api(
            "POST",
            f"/post/{post_d['post_id']}/riprogramma",
            json={"data_ora": nuova_data.isoformat()},
        ).status_code
        == 409  # non è più fallito
    )

    # =========================================================================
    # 7. Scadenze col tick: post scaduto, campagna scaduta, ferma (CA-30, CA-68)
    # =========================================================================
    inizio_e = inizio_d + timedelta(days=7)  # D occupa i 7 giorni precedenti
    e_id, _ = _nuova_campagna(
        api, entra, lavora, "Campagna E", inizio_e, inizio_e + timedelta(days=6)
    )
    entra(OPERATORE)
    # Passa la data di un solo post: quello scade, la campagna resta apribile.
    primo_post_e = min(_post_piano(_vedi(api, e_id)), key=lambda p: p["data_ora"])
    orologio.ora = datetime.fromisoformat(primo_post_e["data_ora"]) + timedelta(days=1)
    _tick()
    entra(OPERATORE)  # sessione scaduta con il salto
    vista_e = _vedi(api, e_id)
    assert vista_e["campagna"]["stato"] == "in_revisione"
    stati_e = [p["stato"] for p in _post_piano(vista_e)]
    assert "scaduto" in stati_e
    assert api("POST", f"/campagne/{e_id}/approva").status_code == 200

    # Campagna F: passa la data di più della metà dei post → scaduta + email.
    inizio_f = inizio_e + timedelta(days=7)  # E è attiva fino al giorno prima
    f_id, _ = _nuova_campagna(
        api, entra, lavora, "Campagna F", inizio_f, inizio_f + timedelta(days=6)
    )
    entra(OPERATORE)
    ultimo_post_f = max(_post_piano(_vedi(api, f_id)), key=lambda p: p["data_ora"])
    orologio.ora = datetime.fromisoformat(ultimo_post_f["data_ora"]) + timedelta(days=1)
    _tick()
    entra(OPERATORE)  # sessione scaduta con il salto
    assert _stato(api, f_id) == "scaduta"
    lavora()
    assert any(
        "scaduta" in e.oggetto.lower() and e.destinatario == ARTIGIANO
        for e in finti.email.inviate
    )

    # Campagna G ferma da 30 minuti in `inviata` (worker spento) → fallita.
    assert entra(ARTIGIANO)
    inizio_g = orologio.ora.date() + timedelta(days=4)
    g_id = api(
        "POST",
        "/campagne",
        json={
            "titolo": "Campagna G",
            "inizio": inizio_g.isoformat(),
            "fine": (inizio_g + timedelta(days=6)).isoformat(),
            "canali": DUE_CANALI,
        },
    ).json()["id"]
    gruppo_g = api(
        "POST",
        f"/campagne/{g_id}/gruppi",
        json={"descrizione": "Foto"},
    ).json()["id"]
    for i in range(4):
        api(
            "POST",
            f"/campagne/{g_id}/foto",
            files={"file": (f"g{i}.jpg", _foto_jpeg(30 + i), "image/jpeg")},
            data={"gruppo_id": str(gruppo_g)},
        )
    assert (
        api(
            "POST",
            f"/campagne/{g_id}/invia",
            json={"dichiarazione": True},
        ).status_code
        == 200
    )
    # Il worker è spento: tolgo il job accodato, la generazione non parte.
    for id_job, job in list(coda.jobs.items()):
        if job["task_name"] == GENERA_CAMPAGNA and job["args"]["campagna_id"] == g_id:
            del coda.jobs[id_job]
    orologio.avanti(timedelta(minutes=35))
    _tick()
    assert _stato(api, g_id) == "generazione_fallita"
    entra(OPERATORE)
    vista_g = _vedi(api, g_id)
    assert vista_g["ultimo_errore"]["tipo"] == "temporaneo"

    # Senza piano e con il giorno di inizio passato → scaduta (CA-30).
    orologio.ora = datetime(
        inizio_g.year, inizio_g.month, inizio_g.day, 10, tzinfo=timezone.utc
    ) + timedelta(days=1)
    _tick()
    entra(OPERATORE)  # sessione scaduta con il salto
    assert _stato(api, g_id) == "scaduta"
    lavora()
    assert any(
        "scaduta" in e.oggetto.lower()
        and e.destinatario == ARTIGIANO
        and "Campagna G" in e.corpo
        for e in finti.email.inviate
    )

    # Due tick di fila non ripetono notifiche né cambi (CA-55).
    n_notifiche = db.scalar(select(func.count(Notifica.id)))
    _tick()
    assert db.scalar(select(func.count(Notifica.id))) == n_notifiche

    # =========================================================================
    # 8. Prove negative di revisione
    # =========================================================================
    assert entra(ARTIGIANO)
    # Ogni intervento di revisione fatto da un artigiano → 403.
    for percorso in ("nota", "respingi", "togli-canale", "sospendi", "annulla"):
        assert api("POST", f"/campagne/{a_id}/{percorso}", json={}).status_code == 403
    assert (
        api(
            "POST",
            f"/post/{post_primo['post_id']}/modifica",
            json={"testo": "x"},
        ).status_code
        == 403
    )

    # Nota o respingi su una campagna ancora in bozza → rifiutato.
    # La bozza la crea l'artigiano; i rifiuti li prova l'operatore.
    assert entra(ARTIGIANO)
    bozza = api(
        "POST",
        "/campagne",
        json={
            "titolo": "Bozza futura",
            "inizio": (orologio.ora.date() + timedelta(days=4)).isoformat(),
            "fine": (orologio.ora.date() + timedelta(days=10)).isoformat(),
            "canali": DUE_CANALI,
        },
    ).json()["id"]
    assert entra(OPERATORE)
    assert api("POST", f"/campagne/{bozza}/nota", json={"nota": "x"}).status_code == 409
    assert (
        api(
            "POST",
            f"/campagne/{bozza}/respingi",
            json={"motivo": "altro", "nota": "x"},
        ).status_code
        == 409
    )
