"""T2a-07: il percorso completo dello sprint 2a, come descritto in converge.md §4.

Verifica l'intero flusso attraverso le API:
1. Artigiano nuovo (senza profilo) -> 404, obbligatorio vuoto -> 422, salvataggio completo (CA-05, CA-07);
2. Artigiano del seed -> Bentornato / Modifica (CA-06);
3. Passo 7 profilo: logo e archivio permanente della bottega, con relative prove negative (CA-78);
4. Campagna A: bozza, modifica bozza PATCH (cambio titolo e fine, data gruppo fuori periodo -> 422, CA-08),
   invio, approvazione, avanzamento temporale di 12 giorni, pubblicazione con marcatura foto.pubblicata_su (CA-76);
5. Campagna B: 4 settimane, fallimento per configurazione AI, cambio nome bottega e logo,
   riprova con AI finta -> in_revisione. Post con foto nuove, foto d'archivio mai uscite e cartoline
   con vecchio nome e vecchio logo dello snapshot immutato (CA-16, CA-77);
6. Campagna C dopo 110 giorni: post riempitivi d'archivio con foto di A uscite da > 90 giorni prima
   delle cartoline; foto di B escluse perché uscite da < 90 giorni (CA-76);
7. Prove negative: modifica campagna non in bozza (409), archivio altrui (404), eliminazione foto
   archivio con n_utilizzi > 0 (409).
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
from app.moduli.accesso import service as accesso_service
from app.moduli.artigiani.models import AccountSocial, ProfiloBottega
from app.moduli.campagne.models import Foto
from app.moduli.contenuti import generazione, jobs

PASSWORD = "PasswordDelSeed!2026"
ARTIGIANO, OPERATORE, ADMIN = (email for email, _, _ in cli.UTENTI_SEED)
BOTTEGA_SEED = cli.PROFILO_SEED["nome"]
DUE_CANALI = ["facebook", "instagram"]

OGGI = datetime(2030, 2, 4, 9, tzinfo=timezone.utc)  # un lunedì mattina
INIZIO = date(2030, 2, 8)  # tra 4 giorni
UNA_SETTIMANA = INIZIO + timedelta(days=6)  # 7 giorni


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
    """Un'ora sola per API, job e tick, che lavorano sulla sessione del test."""
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
    """Esegue i job di generazione in coda come Procrastinate."""
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


def _foto_jpeg(tinta: int, larghezza: int = 1080, altezza: int = 1350) -> bytes:
    """Una foto JPEG valida di dimensioni date."""
    uscita = BytesIO()
    Image.new("RGB", (larghezza, altezza), (tinta % 255, 120, 90)).save(uscita, "JPEG")
    return uscita.getvalue()


def _immagine_logo(
    formato: str = "PNG",
    size: tuple[int, int] = (300, 300),
    colore: str = "red",
) -> bytes:
    """Un file immagine valido per il logo."""
    uscita = BytesIO()
    Image.new("RGB", size, colore).save(uscita, format=formato)
    return uscita.getvalue()


def _dati_scrittura(profilo: dict) -> dict:
    """Estrae solo i campi ammessi in ProfiloScrittura (extra='forbid')."""
    escludi = {"id", "logo", "aggiornato_il", "utente_id"}
    return {k: v for k, v in profilo.items() if k not in escludi}


def _carica_foto_campagna(
    api, campagna_id: int, gruppo_id: int, contenuto: bytes, nome: str = "foto.jpg"
):
    return api(
        "POST",
        f"/campagne/{campagna_id}/foto",
        files={"file": (nome, contenuto, "image/jpeg")},
        data={"gruppo_id": str(gruppo_id)},
    )


def _carica_foto_archivio(
    api, gruppo_id: int, contenuto: bytes, nome: str = "foto.jpg"
):
    return api(
        "POST",
        "/archivio/foto",
        files={"file": (nome, contenuto, "image/jpeg")},
        data={"gruppo_id": str(gruppo_id)},
    )


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


def test_percorso_completo_sprint2a(
    api, client, entra, lavora, orologio, finti, db, coda
):
    """Converge §4, passi 1–7: test completo del percorso dello Sprint 2a."""

    # =========================================================================
    # 1. Artigiano nuovo (crea-utente, senza profilo) -> CA-05, CA-07
    # =========================================================================
    accesso_service.crea_utente(
        db,
        email="nuovo_artigiano@example.com",
        nome="Marco Rossi",
        ruolo="artigiano",
        password=PASSWORD,
    )
    db.commit()

    assert entra("nuovo_artigiano@example.com")["ruolo"] == "artigiano"

    # Senza profilo -> GET /profilo restituisce 404 (CA-05)
    r_profilo = api("GET", "/profilo")
    assert r_profilo.status_code == 404

    # Passo 9 con obbligatorio vuoto non salva e lo indica (CA-07)
    dati_incompleti = {
        "nome": "   ",  # vuoto!
        "referente": "Marco Rossi",
        "citta": "Firenze",
        "tipo_prodotto": "legno_mobili",
        "clienti_ideali": "Appassionati di design",
        "obiettivo": "vendere",
        "canali": ["facebook", "instagram"],
    }
    r_err = api("PUT", "/profilo", json=dati_incompleti)
    assert r_err.status_code == 422
    assert "nome" in r_err.json()["detail"]

    # Profilo completato: salva correttamente ed entra
    dati_completi = dict(dati_incompleti, nome="Bottega del Legno")
    r_ok = api("PUT", "/profilo", json=dati_completi)
    assert r_ok.status_code == 200
    assert r_ok.json()["nome"] == "Bottega del Legno"

    # L'artigiano nuovo non ha canali collegati (sprint 3)
    canali_nuovo = api("GET", "/canali").json()
    assert all(c["collegato"] is False for c in canali_nuovo)

    # =========================================================================
    # 2. Artigiano del seed -> Bentornato / Modifica (CA-06)
    # =========================================================================
    assert entra(ARTIGIANO)["ruolo"] == "artigiano"
    profilo_seed = api("GET", "/profilo").json()
    assert profilo_seed["nome"] == BOTTEGA_SEED
    assert api("GET", "/canali").json() == [
        {"canale": c, "collegato": True} for c in DUE_CANALI
    ]

    # "Modifica" salva senza duplicare la riga sul database (CA-06)
    aggiornato = dict(
        _dati_scrittura(profilo_seed),
        storia="Tre generazioni al tornio: bottega fondata dal nonno.",
    )
    r_aggiorna = api("PUT", "/profilo", json=aggiornato)
    assert r_aggiorna.status_code == 200
    assert (
        db.scalar(select(text("count(*)")).select_from(ProfiloBottega))
        == 2  # nuovo_artigiano + artigiano_seed
    )

    # =========================================================================
    # 3. Passo 7 del profilo: logo e archivio bottega (CA-78)
    # =========================================================================
    # Prove negative logo (CA-78):
    # - PDF
    r_pdf = api(
        "PUT",
        "/profilo/logo",
        files={"file": ("logo.pdf", b"%PDF-1.4\n%finto\n", "application/pdf")},
    )
    assert r_pdf.status_code == 422
    assert "immagine valida" in r_pdf.json()["detail"].lower()

    # - Oltre 2 MB
    r_grande = api(
        "PUT",
        "/profilo/logo",
        files={"file": ("logo.png", b"a" * (2 * 1024 * 1024 + 10), "image/png")},
    )
    assert r_grande.status_code == 422

    # - Lato corto sotto 300 px
    r_stretto = api(
        "PUT",
        "/profilo/logo",
        files={"file": ("stretto.png", _immagine_logo(size=(299, 400)), "image/png")},
    )
    assert r_stretto.status_code == 422

    # Carica logo valido (PNG 300x300)
    logo_iniziale = _immagine_logo("PNG", (300, 300), "red")
    r_logo = api(
        "PUT",
        "/profilo/logo",
        files={"file": ("logo.png", logo_iniziale, "image/png")},
    )
    assert r_logo.status_code == 200
    nome_logo1 = r_logo.json()["logo"]
    assert nome_logo1

    # Sostituisce il logo (JPEG 400x400)
    logo_sostitutivo = _immagine_logo("JPEG", (400, 400), "green")
    r_logo2 = api(
        "PUT",
        "/profilo/logo",
        files={"file": ("logo2.jpg", logo_sostitutivo, "image/jpeg")},
    )
    assert r_logo2.status_code == 200
    nome_logo2 = r_logo2.json()["logo"]
    assert nome_logo2 != nome_logo1

    # Rivede il logo (GET /profilo/logo)
    r_vedi_logo = api("GET", "/profilo/logo")
    assert r_vedi_logo.status_code == 200
    assert r_vedi_logo.content == logo_sostitutivo

    # Archivio permanente bottega: prove negative
    # - Gruppo senza descrizione
    r_gruppo_vuoto = api("POST", "/archivio/gruppi", json={"descrizione": "   "})
    assert r_gruppo_vuoto.status_code == 422

    # Crea gruppo archivio valido
    r_gruppo_arc = api(
        "POST",
        "/archivio/gruppi",
        json={"descrizione": "Capolavori storici di Deruta"},
    )
    assert r_gruppo_arc.status_code == 201
    gruppo_arc_id = r_gruppo_arc.json()["id"]

    # - Foto archivio con lato corto < 1080 px
    foto_piccola = _foto_jpeg(10, larghezza=800, altezza=1200)
    r_foto_piccola = _carica_foto_archivio(api, gruppo_arc_id, foto_piccola)
    assert r_foto_piccola.status_code == 422

    # Carica 2 foto d'archivio valide (1080x1350)
    foto_arc_1 = _carica_foto_archivio(api, gruppo_arc_id, _foto_jpeg(20)).json()["id"]
    foto_arc_2 = _carica_foto_archivio(api, gruppo_arc_id, _foto_jpeg(30)).json()["id"]

    # Rilettura archivio
    elenco_arc = api("GET", "/archivio").json()
    assert len(elenco_arc) == 1
    assert elenco_arc[0]["id"] == gruppo_arc_id
    assert {f["id"] for f in elenco_arc[0]["foto"]} == {foto_arc_1, foto_arc_2}

    # =========================================================================
    # 4. Campagna A (7 giorni, inizio tra 4 giorni, FB e IG, 4 foto in 2 gruppi)
    # =========================================================================
    # Creiamo inizialmente con durata 10 giorni per consentire la verifica del gruppo fuori periodo
    fine_iniziale_a = INIZIO + timedelta(days=9)
    r_camp_a = api(
        "POST",
        "/campagne",
        json={
            "titolo": "Collezione Invernale",
            "inizio": INIZIO.isoformat(),
            "fine": fine_iniziale_a.isoformat(),
            "descrizione": "Ceramiche decorate a mano",
            "canali": DUE_CANALI,
        },
    )
    assert r_camp_a.status_code == 201
    a_id = r_camp_a.json()["id"]

    # Gruppo 1 con data programmata al giorno 8
    data_gruppo_1 = INIZIO + timedelta(days=8)
    g1 = api(
        "POST",
        f"/campagne/{a_id}/gruppi",
        json={
            "descrizione": "Vasi decorati",
            "da_usare_il": data_gruppo_1.isoformat(),
        },
    ).json()["id"]
    fa_1 = _carica_foto_campagna(api, a_id, g1, _foto_jpeg(40)).json()["id"]
    fa_2 = _carica_foto_campagna(api, a_id, g1, _foto_jpeg(50)).json()["id"]

    # Gruppo 2
    g2 = api(
        "POST",
        f"/campagne/{a_id}/gruppi",
        json={"descrizione": "Piatti in maiolica"},
    ).json()["id"]
    fa_3 = _carica_foto_campagna(api, a_id, g2, _foto_jpeg(60)).json()["id"]
    fa_4 = _carica_foto_campagna(api, a_id, g2, _foto_jpeg(70)).json()["id"]
    foto_a = [fa_1, fa_2, fa_3, fa_4]

    # Esce e rientra -> rilettura completa bozza (CA-08)
    entra(ARTIGIANO)
    bozza_a = api("GET", f"/campagne/{a_id}").json()
    assert bozza_a["titolo"] == "Collezione Invernale"
    assert len(bozza_a["gruppi"]) == 2
    assert sum(len(g["foto"]) for g in bozza_a["gruppi"]) == 4

    # Prova negativa: data di gruppo fuori dal nuovo periodo -> 422
    # Anticipiamo la fine al giorno 6 (durata 7 giorni >= 7 giorni), ma il gruppo 1 è al giorno 8!
    fine_7_giorni = INIZIO + timedelta(days=6)
    r_patch_err = api(
        "PATCH",
        f"/campagne/{a_id}",
        json={"fine": fine_7_giorni.isoformat()},
    )
    assert r_patch_err.status_code == 422
    assert "esce dal nuovo periodo" in r_patch_err.json()["detail"].lower()

    # Ripristiniamo la data del gruppo 1 dentro i 7 giorni (giorno 3)
    api(
        "PUT",
        f"/campagne/{a_id}/gruppi/{g1}",
        json={
            "descrizione": "Vasi decorati",
            "da_usare_il": (INIZIO + timedelta(days=3)).isoformat(),
        },
    )

    # Modifica bozza PATCH valida: cambio titolo e fine a 7 giorni (CA-08)
    r_patch_ok = api(
        "PATCH",
        f"/campagne/{a_id}",
        json={
            "titolo": "Collezione Invernale - Riveduta",
            "fine": fine_7_giorni.isoformat(),
        },
    )
    assert r_patch_ok.status_code == 200
    assert r_patch_ok.json()["titolo"] == "Collezione Invernale - Riveduta"
    assert r_patch_ok.json()["fine"] == fine_7_giorni.isoformat()
    assert len(r_patch_ok.json()["gruppi"]) == 2

    # Invio campagna A -> in_revisione
    assert api("POST", f"/campagne/{a_id}/invia").json()["stato"] == "inviata"
    assert lavora() == [1]
    assert _stato(api, a_id) == "in_revisione"

    # Operatore approva
    assert entra(OPERATORE)["ruolo"] == "operatore"
    assert api("POST", f"/campagne/{a_id}/approva").json()["stato"] == "attiva"

    # Data di test avanti di 12 giorni -> pubblicazione e conclusione
    orologio.dopo(UNA_SETTIMANA + timedelta(days=5))
    worker.tick_pubblicazione(0)
    entra(OPERATORE)  # la sessione è scaduta dopo l'avanzamento dell'orologio
    assert _stato(api, a_id) == "conclusa"

    # Nel database ogni foto uscita porta canale e istante (CA-76)
    foto_db_a = list(db.scalars(select(Foto).where(Foto.campagna_id == a_id)))
    assert len(foto_db_a) == 4
    # 3 post chiesti per canale in 1 settimana: almeno 3 foto sono uscite su ogni canale
    uscite_totali = [f for f in foto_db_a if f.pubblicata_su]
    assert len(uscite_totali) >= 3
    for f in uscite_totali:
        for canale, dt_str in f.pubblicata_su.items():
            assert canale in DUE_CANALI
            assert datetime.fromisoformat(dt_str)

    # Identifichiamo quali foto di A non sono uscite su ciascun canale
    foto_mai_uscite_a = {
        canale: [f.id for f in foto_db_a if canale not in f.pubblicata_su]
        for canale in DUE_CANALI
    }
    for canale in DUE_CANALI:
        assert len(foto_mai_uscite_a[canale]) == 1  # 4 foto totali - 3 uscite = 1

    # =========================================================================
    # 5. Campagna B (4 settimane con 4 foto nuove, AI fallita, modifica profilo,
    #                riprova con AI finta, verifica snapshot immutato CA-16, CA-77)
    # =========================================================================
    assert entra(ARTIGIANO)["ruolo"] == "artigiano"
    inizio_b = orologio.ora.date() + timedelta(days=4)
    fine_b = inizio_b + timedelta(days=27)  # 4 settimane = 28 giorni

    r_camp_b = api(
        "POST",
        "/campagne",
        json={
            "titolo": "Primavera d'Arte",
            "inizio": inizio_b.isoformat(),
            "fine": fine_b.isoformat(),
            "descrizione": "Le creazioni primaverili",
            "canali": DUE_CANALI,
        },
    )
    assert r_camp_b.status_code == 201
    b_id = r_camp_b.json()["id"]

    gb = api(
        "POST",
        f"/campagne/{b_id}/gruppi",
        json={"descrizione": "Nuove ceramiche primaverili"},
    ).json()["id"]
    foto_b_nuove = [
        _carica_foto_campagna(api, b_id, gb, _foto_jpeg(80 + 10 * i)).json()["id"]
        for i in range(4)
    ]

    # Inviata con errore configurazione AI -> generazione fallita
    finti.ai.comanda_errore("analizza_gruppo", "configurazione", volte=None)
    assert api("POST", f"/campagne/{b_id}/invia").status_code == 200
    assert lavora() == [1]
    assert _stato(api, b_id) == "generazione_fallita"

    # L'artigiano cambia il nome della bottega e il logo
    nome_bottega_modificato = "Ceramiche Bianchi & Figli Rinnovate"
    profilo_aggiornato = dict(
        _dati_scrittura(api("GET", "/profilo").json()),
        nome=nome_bottega_modificato,
    )
    assert api("PUT", "/profilo", json=profilo_aggiornato).status_code == 200

    logo_nuovo = _immagine_logo("PNG", (350, 350), "yellow")
    r_nuovo_logo = api(
        "PUT",
        "/profilo/logo",
        files={"file": ("logo_nuovo.png", logo_nuovo, "image/png")},
    )
    assert r_nuovo_logo.status_code == 200
    nome_logo_nuovo = r_nuovo_logo.json()["logo"]

    # Torna l'AI finta, l'operatore preme Riprova -> in_revisione
    assert entra(OPERATORE)["ruolo"] == "operatore"
    finti.ai._errori.clear()
    riprova = api("POST", f"/campagne/{b_id}/riprova")
    assert riprova.status_code == 200
    assert riprova.json()["stato"] == "inviata"
    assert lavora() == [1]
    assert _stato(api, b_id) == "in_revisione"

    # Verifica snapshot immutato (CA-16, CA-77)
    dettaglio_b = api("GET", f"/campagne/{b_id}").json()
    assert dettaglio_b["profilo_snapshot"]["nome"] == BOTTEGA_SEED
    assert dettaglio_b["profilo_snapshot"]["logo"] == nome_logo2
    assert dettaglio_b["profilo_snapshot"]["logo"] != nome_logo_nuovo

    # Vedi campagna: 12 post per canale
    vista_b = _vedi(api, b_id)
    per_canale_b = _post_per_canale(vista_b)
    for canale, post_canale in per_canale_b.items():
        assert len(post_canale) == 12
        post_foto = [p for p in post_canale if p["riempitivo"] is None]
        post_cartoline = [p for p in post_canale if p["riempitivo"] == "cartolina"]
        # 4 foto nuove + 2 archivio permanente + 1 di A mai uscita lì = 7 foto
        assert len(post_foto) == 7
        assert len(post_cartoline) == 5

        foto_usate = [f_id for p in post_foto for f_id in _foto_del_post(p)]
        # Nessuna foto compare due volte sullo stesso canale
        assert len(foto_usate) == len(set(foto_usate))
        # Contiene le 4 nuove di B
        assert set(foto_b_nuove).issubset(set(foto_usate))
        # Contiene le 2 di archivio permanente
        assert {foto_arc_1, foto_arc_2}.issubset(set(foto_usate))
        # Contiene quella di A mai uscita su questo canale
        f_mai_uscita = foto_mai_uscite_a[canale][0]
        assert f_mai_uscita in foto_usate
        # Nessuna foto di A uscita su questo canale in Campagna A compare qui!
        uscite_in_a = [f.id for f in foto_db_a if canale in f.pubblicata_su]
        assert not any(f_a in foto_usate for f_a in uscite_in_a)

    # Operatore approva campagna B
    assert api("POST", f"/campagne/{b_id}/approva").status_code == 200
    assert _stato(api, b_id) == "attiva"

    # =========================================================================
    # 6. Campagna C: orologio avanti di 110 giorni (B conclusa)
    #    Tra i riempitivi compaiono post archivio con le foto di A (> 90 gg) (CA-76)
    # =========================================================================
    orologio.ora = orologio.ora + timedelta(days=110)
    worker.tick_pubblicazione(0)
    entra(OPERATORE)  # la sessione è scaduta dopo l'avanzamento dell'orologio
    assert _stato(api, b_id) == "conclusa"

    assert entra(ARTIGIANO)["ruolo"] == "artigiano"
    inizio_c = orologio.ora.date() + timedelta(days=4)
    fine_c = inizio_c + timedelta(days=27)  # 4 settimane = 28 giorni

    r_camp_c = api(
        "POST",
        "/campagne",
        json={
            "titolo": "Campagna d'Estate",
            "inizio": inizio_c.isoformat(),
            "fine": fine_c.isoformat(),
            "descrizione": "Ceramiche per l'estate",
            "canali": DUE_CANALI,
        },
    )
    assert r_camp_c.status_code == 201
    c_id = r_camp_c.json()["id"]

    gc = api(
        "POST",
        f"/campagne/{c_id}/gruppi",
        json={"descrizione": "Nuove creazioni estive"},
    ).json()["id"]
    for i in range(4):
        _carica_foto_campagna(api, c_id, gc, _foto_jpeg(150 + 10 * i))

    assert api("POST", f"/campagne/{c_id}/invia").status_code == 200
    assert lavora() == [1]
    assert _stato(api, c_id) == "piano_da_rivedere"

    # L'operatore visualizza il piano debole e preme Prosegui
    assert entra(OPERATORE)["ruolo"] == "operatore"
    assert api("POST", f"/campagne/{c_id}/prosegui").status_code == 200
    assert lavora() == [1]
    assert _stato(api, c_id) == "in_revisione"

    vista_c = _vedi(api, c_id)
    per_canale_c = _post_per_canale(vista_c)
    for canale, post_canale in per_canale_c.items():
        assert len(post_canale) == 12
        riempitivi_archivio = [p for p in post_canale if p["riempitivo"] == "archivio"]
        riempitivi_cartolina = [
            p for p in post_canale if p["riempitivo"] == "cartolina"
        ]

        # Tra i riempitivi compaiono post archivio prima delle cartoline (CA-76)
        assert len(riempitivi_archivio) > 0
        assert len(riempitivi_cartolina) > 0

        # L'indice del primo post archivio precede l'indice del primo post cartolina
        idx_primo_archivio = min(post_canale.index(p) for p in riempitivi_archivio)
        idx_primo_cartolina = min(post_canale.index(p) for p in riempitivi_cartolina)
        assert idx_primo_archivio < idx_primo_cartolina

        # I post archivio usano le foto di A (uscite da > 90 giorni)
        foto_nei_post_archivio = [
            f_id for p in riempitivi_archivio for f_id in _foto_del_post(p)
        ]
        assert all(f_id in foto_a for f_id in foto_nei_post_archivio)

        # Le foto uscite in B (uscite da meno di 90 giorni) non compaiono!
        assert not any(f_id in foto_b_nuove for f_id in foto_nei_post_archivio)

    # =========================================================================
    # 7. Prove negative dello Sprint 2a
    # =========================================================================
    assert entra(ARTIGIANO)["ruolo"] == "artigiano"

    # Modifica di campagna non in bozza -> 409
    assert (
        api(
            "PATCH",
            f"/campagne/{a_id}",
            json={"titolo": "Modifica vietata"},
        ).status_code
        == 409
    )
    assert (
        api(
            "PATCH",
            f"/campagne/{b_id}",
            json={"titolo": "Modifica vietata"},
        ).status_code
        == 409
    )

    # Archivio di un altro artigiano -> 404
    assert entra("nuovo_artigiano@example.com")["ruolo"] == "artigiano"
    # Prova ad accedere/eliminare il gruppo dell'archivio del seed
    r_del_gruppo_altrui = api("DELETE", f"/archivio/gruppi/{gruppo_arc_id}")
    assert r_del_gruppo_altrui.status_code == 404
    r_del_foto_altrui = api("DELETE", f"/archivio/foto/{foto_arc_1}")
    assert r_del_foto_altrui.status_code == 404

    # Eliminazione foto d'archivio già usata in un post (n_utilizzi > 0) -> 409
    assert entra(ARTIGIANO)["ruolo"] == "artigiano"
    # foto_arc_1 è stata usata nella campagna B e/o C
    r_del_usata = api("DELETE", f"/archivio/foto/{foto_arc_1}")
    assert r_del_usata.status_code == 409
    assert "utilizzata" in r_del_usata.json()["detail"].lower()


def test_prove_negative_del_percorso_sprint2a(api, entra, lavora, db, finti):
    """Converge §4 passo 7 e §3 passo 6: ogni rifiuto ha il suo codice e un messaggio in italiano."""
    assert entra(ARTIGIANO)["ruolo"] == "artigiano"

    def crea(inizio: date, fine: date):
        return api(
            "POST",
            "/campagne",
            json={
                "titolo": "Prova Negative",
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

    # Creazione campagna in bozza con 3 foto
    r_camp = api(
        "POST",
        "/campagne",
        json={
            "titolo": "Bozza con 3 foto",
            "inizio": INIZIO.isoformat(),
            "fine": UNA_SETTIMANA.isoformat(),
            "canali": DUE_CANALI,
        },
    )
    campagna_id = r_camp.json()["id"]
    gruppo_id = api(
        "POST",
        f"/campagne/{campagna_id}/gruppi",
        json={"descrizione": "Gruppo di prova"},
    ).json()["id"]

    for _ in range(3):
        assert (
            _carica_foto_campagna(
                api, campagna_id, gruppo_id, _foto_jpeg(90)
            ).status_code
            == 201
        )

    pdf = _carica_foto_campagna(
        api, campagna_id, gruppo_id, b"%PDF-1.4\n%finto\n", nome="foto.pdf"
    )
    rifiutata(pdf, 422)  # un PDF come foto
    rifiutata(
        api("POST", f"/campagne/{campagna_id}/invia"), 422
    )  # invio con solo 3 foto

    # L'artigiano non entra nelle funzioni dell'operatore, l'admin sì
    rifiutata(api("POST", f"/campagne/{campagna_id}/approva"), 403)
    assert entra(ADMIN)["ruolo"] == "admin"
    rifiutata(api("POST", f"/campagne/{campagna_id}/approva"), 409)

    assert entra(ARTIGIANO)["ruolo"] == "artigiano"
    assert (
        _carica_foto_campagna(api, campagna_id, gruppo_id, _foto_jpeg(200)).status_code
        == 201
    )
    _account(db, "instagram").stato = "scollegato"
    db.commit()
    rifiutata(api("POST", f"/campagne/{campagna_id}/invia"), 409)  # scollegato dopo
    _account(db, "instagram").stato = "collegato"
    db.commit()

    # Errore di configurazione dell'AI: fallita subito, senza altre esecuzioni
    finti.ai.comanda_errore("analizza_gruppo", "configurazione", volte=None)
    assert api("POST", f"/campagne/{campagna_id}/invia").status_code == 200
    assert lavora() == [1]
    assert entra(OPERATORE)["ruolo"] == "operatore"
    vista = _vedi(api, campagna_id)
    assert vista["campagna"]["stato"] == "generazione_fallita"
    assert (vista["ultimo_errore"]["tipo"], vista["ultimo_errore"]["tappa"]) == (
        "configurazione",
        "analisi",
    )
