"""Test per la modifica della bozza di campagna (T2a-21).

Verifica i criteri di accettazione:
- CA-08: bozza aperta -> modifica e rilettura completa (dati, canali, gruppi, foto)
- CA-09: modifica con data inizio < oggi + 3 giorni -> 422
- CA-10: modifica con durata > 92 giorni, < 7 giorni o fine <= inizio -> 422
- CA-48: modifica con canale non collegato -> 422
- Modifica fuori dallo stato bozza -> 409
- Modifica con data di un gruppo che esce dal nuovo periodo (R-13) -> 422
- Modifica campagna altrui o inesistente -> 404
- Modifica con ruolo operatore o admin -> 403
- Modifica sovrapposta ad altra campagna aperta dell'artigiano -> 409
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.core.orologio import adesso
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_attiva,
    campagna_in_bozza,
    campagna_inviata,
    foto,
    gruppo,
)


def test_ca08_modifica_bozza_successo_restituisce_dettaglio_completo(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-08: PATCH /campagne/{id} aggiorna la bozza e restituisce il dettaglio completo con dati, canali, gruppi e foto."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["facebook", "instagram"])

    oggi = adesso().date()
    inizio_iniziale = oggi + timedelta(days=5)
    fine_iniziale = inizio_iniziale + timedelta(days=14)

    c = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        titolo="Titolo Iniziale",
        descrizione="Descrizione iniziale",
        inizio=inizio_iniziale,
        fine=fine_iniziale,
        canali=["facebook"],
    )

    # Aggiungiamo un gruppo con foto alla bozza
    g = gruppo(
        db,
        c,
        descrizione="Gruppo prodotti",
        da_usare_il=inizio_iniziale + timedelta(days=2),
    )
    foto(db, gruppo=g)

    # Nuovi valori validi
    nuovo_inizio = oggi + timedelta(days=4)
    nuovo_fine = nuovo_inizio + timedelta(days=20)
    payload = {
        "titolo": "Nuovo Titolo Modificato",
        "inizio": nuovo_inizio.isoformat(),
        "fine": nuovo_fine.isoformat(),
        "descrizione": "Nuova descrizione aggiornata",
        "canali": ["facebook", "instagram"],
    }

    risposta = client.patch(f"/api/campagne/{c.id}", json=payload)
    assert risposta.status_code == 200

    corpo = risposta.json()
    assert corpo["id"] == c.id
    assert corpo["titolo"] == "Nuovo Titolo Modificato"
    assert corpo["inizio"] == nuovo_inizio.isoformat()
    assert corpo["fine"] == nuovo_fine.isoformat()
    assert corpo["descrizione"] == "Nuova descrizione aggiornata"
    assert set(corpo["canali"]) == {"facebook", "instagram"}
    assert corpo["stato"] == "bozza"

    # CA-08: la bozza riletta ha gruppi e foto
    assert len(corpo["gruppi"]) == 1
    assert corpo["gruppi"][0]["id"] == g.id
    assert corpo["gruppi"][0]["descrizione"] == "Gruppo prodotti"
    assert len(corpo["gruppi"][0]["foto"]) == 1

    # Rilettura via GET per verificare persistenza
    rilettura = client.get(f"/api/campagne/{c.id}")
    assert rilettura.status_code == 200
    assert rilettura.json()["titolo"] == "Nuovo Titolo Modificato"
    assert set(rilettura.json()["canali"]) == {"facebook", "instagram"}


def test_modifica_bozza_parziale(client: TestClient, utente_di_prova, db: Session):
    """Modifica parziale: aggiornare solo il titolo o solo la descrizione mantiene intatti gli altri campi."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["facebook", "instagram"])

    oggi = adesso().date()
    inizio = oggi + timedelta(days=10)
    fine = inizio + timedelta(days=14)

    c = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        titolo="Titolo Originale",
        descrizione="Descrizione Originale",
        inizio=inizio,
        fine=fine,
        canali=["facebook"],
    )

    # Modifica solo del titolo
    risposta = client.patch(
        f"/api/campagne/{c.id}", json={"titolo": "Solo Titolo Aggiornato"}
    )
    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["titolo"] == "Solo Titolo Aggiornato"
    assert corpo["descrizione"] == "Descrizione Originale"
    assert corpo["inizio"] == inizio.isoformat()
    assert corpo["fine"] == fine.isoformat()
    assert corpo["canali"] == ["facebook"]

    # Modifica solo della descrizione
    risposta_desc = client.patch(
        f"/api/campagne/{c.id}", json={"descrizione": "Solo Descrizione Nuova"}
    )
    assert risposta_desc.status_code == 200
    assert risposta_desc.json()["descrizione"] == "Solo Descrizione Nuova"
    assert risposta_desc.json()["titolo"] == "Solo Titolo Aggiornato"


def test_ca48_modifica_canale_non_collegato_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-48: Modifica con un canale privo di account collegato deve fallire con 422."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(
        db, utente_id=artigiano.id, canali=["facebook"]
    )  # solo facebook collegato

    oggi = adesso().date()
    c = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        inizio=oggi + timedelta(days=5),
        fine=oggi + timedelta(days=15),
        canali=["facebook"],
    )

    payload = {"canali": ["facebook", "instagram"]}
    risposta = client.patch(f"/api/campagne/{c.id}", json=payload)
    assert risposta.status_code == 422
    assert "non sono collegati" in risposta.json()["detail"]


def test_ca09_modifica_inizio_troppo_vicino_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-09: Modifica con data inizio < oggi + 3 giorni deve fallire con 422."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["facebook"])

    oggi = adesso().date()
    c = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        inizio=oggi + timedelta(days=10),
        fine=oggi + timedelta(days=20),
        canali=["facebook"],
    )

    inizio_vietato = oggi + timedelta(days=2)
    payload = {"inizio": inizio_vietato.isoformat()}
    risposta = client.patch(f"/api/campagne/{c.id}", json=payload)
    assert risposta.status_code == 422
    assert "almeno 3 giorni" in risposta.json()["detail"]


def test_ca10_modifica_durata_non_valida_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-10: Modifica con durata < 7 giorni, > 92 giorni o fine <= inizio deve fallire con 422."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["facebook"])

    oggi = adesso().date()
    inizio = oggi + timedelta(days=10)
    fine = inizio + timedelta(days=14)

    c = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        inizio=inizio,
        fine=fine,
        canali=["facebook"],
    )

    # Durata troppo corta: 5 giorni (< 7)
    fine_troppo_corta = inizio + timedelta(days=4)
    risposta_corta = client.patch(
        f"/api/campagne/{c.id}", json={"fine": fine_troppo_corta.isoformat()}
    )
    assert risposta_corta.status_code == 422
    assert "almeno 7 giorni" in risposta_corta.json()["detail"]

    # Durata troppo lunga: 100 giorni (> 92)
    fine_troppo_lunga = inizio + timedelta(days=99)
    risposta_lunga = client.patch(
        f"/api/campagne/{c.id}", json={"fine": fine_troppo_lunga.isoformat()}
    )
    assert risposta_lunga.status_code == 422
    assert "non può superare 92 giorni" in risposta_lunga.json()["detail"]

    # Fine precedente all'inizio
    risposta_retroattiva = client.patch(
        f"/api/campagne/{c.id}",
        json={
            "inizio": (inizio + timedelta(days=20)).isoformat(),
            "fine": inizio.isoformat(),
        },
    )
    assert risposta_retroattiva.status_code == 422
    assert "successiva alla data di inizio" in risposta_retroattiva.json()["detail"]


def test_modifica_bozza_data_gruppo_fuori_periodo_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """R-13: Se la data di un gruppo (da_usare_il) esce dal nuovo periodo della campagna -> 422."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["facebook"])

    oggi = adesso().date()
    inizio = oggi + timedelta(days=10)
    fine = inizio + timedelta(days=20)

    c = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        inizio=inizio,
        fine=fine,
        canali=["facebook"],
    )

    # Gruppo con data programmata al giorno inizio + 15
    giorno_gruppo = inizio + timedelta(days=15)
    gruppo(db, c, da_usare_il=giorno_gruppo)

    # Tentiamo di anticipare la fine al giorno inizio + 10 (il gruppo rimarrebbe fuori!)
    nuova_fine = inizio + timedelta(days=10)
    risposta = client.patch(
        f"/api/campagne/{c.id}", json={"fine": nuova_fine.isoformat()}
    )
    assert risposta.status_code == 422
    assert "esce dal nuovo periodo" in risposta.json()["detail"]

    # Tentiamo di posticipare l'inizio oltre il giorno del gruppo (es. giorno inizio + 16)
    nuovo_inizio = giorno_gruppo + timedelta(days=1)
    risposta_inizio = client.patch(
        f"/api/campagne/{c.id}",
        json={
            "inizio": nuovo_inizio.isoformat(),
            "fine": (nuovo_inizio + timedelta(days=10)).isoformat(),
        },
    )
    assert risposta_inizio.status_code == 422
    assert "esce dal nuovo periodo" in risposta_inizio.json()["detail"]


def test_modifica_fuori_dalla_bozza_da_409(
    client: TestClient, utente_di_prova, db: Session
):
    """Modifica di una campagna non in stato bozza (es. inviata) fallisce con 409."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["facebook"])

    c_inviata = campagna_inviata(db, profilo_id=bottega.id)

    risposta = client.patch(
        f"/api/campagne/{c_inviata.id}", json={"titolo": "Titolo Invalido"}
    )
    assert risposta.status_code == 409
    assert "solo quando è in bozza" in risposta.json()["detail"]


def test_modifica_campagna_altrui_da_404(
    client: TestClient, utente_di_prova, db: Session
):
    """Artigiano che tenta di modificare una campagna altrui o inesistente riceve 404."""
    proprietario = utente_di_prova("artigiano")
    bottega_a = profilo(db, utente_id=proprietario.id, canali=["facebook"])
    c = campagna_in_bozza(db, profilo_id=bottega_a.id)

    estraneo = utente_di_prova("artigiano")
    profilo(db, utente_id=estraneo.id, canali=["facebook"])

    # Estraneo riceve 404
    risposta_estraneo = client.patch(
        f"/api/campagne/{c.id}", json={"titolo": "Tentativo Hacking"}
    )
    assert risposta_estraneo.status_code == 404
    assert risposta_estraneo.json() == {"detail": "Campagna non trovata."}

    # ID inesistente riceve 404
    risposta_inesistente = client.patch(
        "/api/campagne/999999", json={"titolo": "Ghost"}
    )
    assert risposta_inesistente.status_code == 404


def test_modifica_ruolo_non_autorizzato_da_403(
    client: TestClient, utente_di_prova, db: Session
):
    """Operatore o admin che tentano di modificare una bozza ricevono 403."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["facebook"])
    c = campagna_in_bozza(db, profilo_id=bottega.id)

    utente_di_prova("operatore")
    risposta = client.patch(
        f"/api/campagne/{c.id}", json={"titolo": "Modifica Operatore"}
    )
    assert risposta.status_code == 403


def test_modifica_sovrapposizione_con_altra_campagna_da_409(
    client: TestClient, utente_di_prova, db: Session
):
    """Modifica che crea sovrapposizione con un'altra campagna aperta dello stesso artigiano fallisce con 409."""
    artigiano = utente_di_prova("artigiano")
    bottega = profilo(db, utente_id=artigiano.id, canali=["facebook"])

    oggi = adesso().date()

    # Campagna attiva dal giorno 20 al giorno 35
    inizio_attiva = oggi + timedelta(days=20)
    fine_attiva = inizio_attiva + timedelta(days=15)
    campagna_attiva(
        db,
        profilo_id=bottega.id,
        inizio=inizio_attiva,
        fine=fine_attiva,
    )

    # Bozza dal giorno 5 al giorno 15 (non sovrapposta)
    inizio_bozza = oggi + timedelta(days=5)
    fine_bozza = inizio_bozza + timedelta(days=10)
    c_bozza = campagna_in_bozza(
        db,
        profilo_id=bottega.id,
        inizio=inizio_bozza,
        fine=fine_bozza,
    )

    # Estendiamo la bozza fino a sovrapporsi alla campagna attiva (fine al giorno 22)
    fine_sovrapposta = inizio_attiva + timedelta(days=2)
    risposta = client.patch(
        f"/api/campagne/{c_bozza.id}", json={"fine": fine_sovrapposta.isoformat()}
    )
    assert risposta.status_code == 409
    assert "si sovrappone" in risposta.json()["detail"]
