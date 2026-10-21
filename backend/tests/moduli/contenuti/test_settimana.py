"""Test di ``GET /calendario``, il calendario settimanale (T3-73, spec R-45, R-48, CA-97, CA-98)."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.core.orologio import ROMA, adesso
from app.main import app
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_da_approvare

# Lunedì 7 gennaio 2030, a Roma UTC+1.
LUNEDI = date(2030, 1, 7)
MERCOLEDI_ORA = datetime(2030, 1, 9, 10, tzinfo=timezone.utc)


def _post(db: Session, campagna, stato: str, quando: datetime):
    return post_da_approvare(db, campagna_id=campagna.id, stato=stato, data_ora=quando)


def _ids(risposta) -> list[int]:
    return [p["id"] for g in risposta.json()["giorni"] for p in g["post"]]


def test_ca97_artigiano_solo_i_suoi_post_negli_stati_visibili(
    db: Session, client: TestClient, utente_di_prova
):
    proprietario = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=proprietario.id, nome="Ceramiche Rossi")
    prima = campagna_attiva(db, profilo_id=bottega.id, titolo="Primavera")
    seconda = campagna_attiva(db, profilo_id=bottega.id, titolo="Saldi")
    martedi = datetime(2030, 1, 8, 9, tzinfo=timezone.utc)
    giovedi = datetime(2030, 1, 10, 15, tzinfo=timezone.utc)

    visibili = [
        _post(db, prima, "approvato", martedi),
        _post(db, prima, "pubblicato", martedi + timedelta(hours=1)),
        _post(db, seconda, "fallito", giovedi),
        _post(db, seconda, "annullato", giovedi + timedelta(hours=1)),
    ]
    # Mai nel calendario: gli altri stati del post...
    for stato in ("da_approvare", "scartato", "scaduto"):
        _post(db, prima, stato, martedi)
    # ...i post di una campagna non approvata...
    _post(db, campagna_in_revisione(db, profilo_id=bottega.id), "approvato", martedi)
    # ...e quelli di un altro artigiano.
    altro = utente(db, "artigiano")
    altra = campagna_attiva(db, profilo_id=profilo(db, utente_id=altro.id).id)
    _post(db, altra, "approvato", martedi)

    risposta = client.get("/api/calendario", params={"dal": LUNEDI.isoformat()})
    assert risposta.status_code == 200
    assert risposta.headers["Cache-Control"] == "no-store"
    assert _ids(risposta) == [p.id for p in visibili]

    primo = risposta.json()["giorni"][1]["post"][0]  # martedì
    assert primo["campagna_id"] == prima.id
    assert primo["campagna_titolo"] == "Primavera"
    assert primo["bottega"] == "Ceramiche Rossi"
    # Gli stessi campi del calendario della campagna.
    assert primo["canale"] == "instagram"
    assert primo["testo"] == "Testo di prova"
    assert primo["hashtag"] == ["artigianato"]
    assert primo["ora"] == "10:00"
    assert primo["foto"][0]["url"].startswith("/api/foto/")


def test_ca97_sette_giorni_anche_vuoti(
    db: Session, client: TestClient, utente_di_prova
):
    utente_di_prova("artigiano")
    risposta = client.get("/api/calendario", params={"dal": LUNEDI.isoformat()})
    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["dal"] == "2030-01-07"
    assert corpo["al"] == "2030-01-13"
    assert [g["data"] for g in corpo["giorni"]] == [
        (LUNEDI + timedelta(days=i)).isoformat() for i in range(7)
    ]
    assert all(g["post"] == [] for g in corpo["giorni"])


def test_ca97_senza_dal_la_settimana_di_oggi(
    db: Session, client: TestClient, utente_di_prova
):
    proprietario = utente_di_prova("artigiano")
    campagna = campagna_attiva(db, profilo_id=profilo(db, utente_id=proprietario.id).id)
    di_oggi = _post(
        db, campagna, "approvato", datetime(2030, 1, 11, 9, tzinfo=timezone.utc)
    )
    _post(db, campagna, "approvato", datetime(2030, 1, 15, 9, tzinfo=timezone.utc))
    app.dependency_overrides[adesso] = lambda: MERCOLEDI_ORA

    risposta = client.get("/api/calendario")
    assert risposta.status_code == 200
    assert risposta.json()["dal"] == "2030-01-07"
    assert risposta.json()["al"] == "2030-01-13"
    assert _ids(risposta) == [di_oggi.id]


def test_ca98_operatore_tutti_gli_artigiani_con_la_bottega(
    db: Session, client: TestClient, utente_di_prova
):
    utente_di_prova("operatore")
    quando = datetime(2030, 1, 8, 9, tzinfo=timezone.utc)
    a = profilo(db, nome="Bottega A")
    b = profilo(db, nome="Bottega B")
    del_a = _post(db, campagna_attiva(db, profilo_id=a.id), "approvato", quando)
    del_b = _post(
        db,
        campagna_attiva(db, profilo_id=b.id),
        "pubblicato",
        quando + timedelta(hours=2),
    )

    risposta = client.get("/api/calendario", params={"dal": LUNEDI.isoformat()})
    assert risposta.status_code == 200
    mie = {del_a.id, del_b.id}
    post = [p for g in risposta.json()["giorni"] for p in g["post"] if p["id"] in mie]
    assert [(p["id"], p["bottega"]) for p in post] == [
        (del_a.id, "Bottega A"),
        (del_b.id, "Bottega B"),
    ]

    utente_di_prova("admin")
    dell_admin = _ids(client.get("/api/calendario", params={"dal": "2030-01-07"}))
    assert [i for i in dell_admin if i in mie] == [del_a.id, del_b.id]


def test_ca98_dal_non_lunedi_422(db: Session, client: TestClient, utente_di_prova):
    utente_di_prova("operatore")
    risposta = client.get("/api/calendario", params={"dal": "2030-01-08"})
    assert risposta.status_code == 422
    assert risposta.json() == {"detail": "La settimana comincia di lunedì."}
    # Una data scritta male è comunque un 422.
    assert client.get("/api/calendario", params={"dal": "domani"}).status_code == 422


def test_ca98_confine_di_settimana_in_europe_rome(
    db: Session, client: TestClient, utente_di_prova
):
    """Contano i giorni di Roma, non quelli UTC (R-48)."""
    utente_di_prova("operatore")
    campagna = campagna_attiva(db, profilo_id=profilo(db).id)

    def a_roma(giorno: date, ore: int, minuti: int) -> datetime:
        return datetime(
            giorno.year, giorno.month, giorno.day, ore, minuti, tzinfo=ROMA
        ).astimezone(timezone.utc)

    domenica = _post(db, campagna, "approvato", a_roma(date(2030, 1, 13), 23, 30))
    lunedi_presto = _post(db, campagna, "approvato", a_roma(LUNEDI, 0, 30))
    # Appena fuori: lunedì 14 alle 00:30 a Roma è ancora domenica per l'UTC.
    fuori = _post(db, campagna, "approvato", a_roma(date(2030, 1, 14), 0, 30))
    prima = _post(db, campagna, "approvato", a_roma(date(2030, 1, 6), 23, 30))

    mie = {domenica.id, lunedi_presto.id, fuori.id, prima.id}

    def giorni_di(dal: str) -> dict[str, list[int]]:
        corpo = client.get("/api/calendario", params={"dal": dal}).json()
        return {
            g["data"]: [p["id"] for p in g["post"] if p["id"] in mie]
            for g in corpo["giorni"]
        }

    giorni = giorni_di("2030-01-07")
    assert giorni["2030-01-07"] == [lunedi_presto.id]
    assert giorni["2030-01-13"] == [domenica.id]
    assert fuori.id not in sum(giorni.values(), [])
    assert prima.id not in sum(giorni.values(), [])

    successiva = giorni_di("2030-01-14")
    assert sum(successiva.values(), []) == [fuori.id]
