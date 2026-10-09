"""Test per le API di creazione, elenco e dettaglio delle campagne (T1-22).

Verifica i criteri di accettazione:
- CA-04: artigiano accede a campagna o foto altrui -> 404 (non 403)
- CA-09: inizio < oggi + 3 giorni -> 422
- CA-10: durata > 92 giorni, < 7 giorni o fine <= inizio -> 422
- CA-11: bozza esistente per lo stesso artigiano -> 409
- CA-12: periodo sovrapposto con campagna attiva/in corso -> 409; se respinta o scaduta -> ok
- CA-48: canali non collegati alla creazione bozza -> 422
- CA-54: dettaglio bozza con avvisi informativi (foto_poche, riempitivi_molti, frequenza_alta)
- Elenco con due stati insieme (filtro ripetibile ?stato=) e bottega/citta per l'operatore
- Ruoli e permessi: POST riservato ad artigiano (403 ad altri ruoli).
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.core.orologio import ROMA, adesso
from app.moduli.campagne import domain
from tests.moduli.artigiani.fabbrica import account_social, profilo
from tests.moduli.campagne.fabbrica import (
    campagna_in_bozza,
    campagna_inviata,
    foto,
    gruppo,
)


def test_ca04_artigiano_accede_a_campagna_altrui_da_404(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-04: L'artigiano che tenta di consultare una campagna altrui riceve 404."""
    artigiano_a = utente_di_prova("artigiano")
    profilo_a = profilo(db, utente_id=artigiano_a.id)
    c_a = campagna_in_bozza(db, profilo_id=profilo_a.id, titolo="Campagna A")

    risposta_proprietario = client.get(f"/api/campagne/{c_a.id}")
    assert risposta_proprietario.status_code == 200
    assert risposta_proprietario.json()["id"] == c_a.id
    assert risposta_proprietario.json()["titolo"] == "Campagna A"

    artigiano_b = utente_di_prova("artigiano")
    profilo(db, utente_id=artigiano_b.id)

    risposta_estraneo = client.get(f"/api/campagne/{c_a.id}")
    assert risposta_estraneo.status_code == 404
    assert risposta_estraneo.json() == {"detail": "Campagna non trovata."}


def test_ca09_creazione_inizio_troppo_vicino_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-09: Data inizio < oggi + 3 giorni deve fallire con 422."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id, canali=["instagram"])

    oggi = adesso().date()
    inizio_non_valido = oggi + timedelta(days=2)
    fine = inizio_non_valido + timedelta(days=10)

    payload = {
        "titolo": "Campagna troppo anticipata",
        "inizio": inizio_non_valido.isoformat(),
        "fine": fine.isoformat(),
        "descrizione": "Descrizione di prova",
        "canali": ["instagram"],
    }
    risposta = client.post("/api/campagne", json=payload)
    assert risposta.status_code == 422
    assert "almeno 3 giorni" in risposta.json()["detail"]


def test_ca10_durata_superiore_92_giorni_o_fine_prima_inizio_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-10: Durata > 92 giorni, < 7 giorni o fine <= inizio deve fallire con 422."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id, canali=["instagram"])

    oggi = adesso().date()
    inizio_valido = oggi + timedelta(days=5)

    # 1. Fine precedente a inizio
    risposta_fine_precedente = client.post(
        "/api/campagne",
        json={
            "titolo": "Date invertite",
            "inizio": inizio_valido.isoformat(),
            "fine": (inizio_valido - timedelta(days=1)).isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta_fine_precedente.status_code == 422
    assert "successiva alla data di inizio" in risposta_fine_precedente.json()["detail"]

    # 2. Fine uguale a inizio
    risposta_fine_uguale = client.post(
        "/api/campagne",
        json={
            "titolo": "Date identiche",
            "inizio": inizio_valido.isoformat(),
            "fine": inizio_valido.isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta_fine_uguale.status_code == 422

    # 3. Durata inferiore a 7 giorni (es. 5 giorni)
    risposta_troppo_corta = client.post(
        "/api/campagne",
        json={
            "titolo": "Troppo corta",
            "inizio": inizio_valido.isoformat(),
            "fine": (inizio_valido + timedelta(days=4)).isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta_troppo_corta.status_code == 422
    assert "almeno 7 giorni" in risposta_troppo_corta.json()["detail"]

    # 4. Durata superiore a 92 giorni: 93 giorni compresi inizio e fine
    risposta_troppo_lunga = client.post(
        "/api/campagne",
        json={
            "titolo": "Troppo lunga",
            "inizio": inizio_valido.isoformat(),
            "fine": (inizio_valido + timedelta(days=92)).isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta_troppo_lunga.status_code == 422
    assert "superare 92 giorni" in risposta_troppo_lunga.json()["detail"]


def test_ca11_bozza_esistente_nuova_bozza_da_409(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-11: Se l'artigiano ha già una bozza aperta, un'altra bozza dà 409."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id, canali=["instagram"])

    oggi = adesso().date()
    inizio1 = oggi + timedelta(days=5)
    fine1 = inizio1 + timedelta(days=10)

    risposta1 = client.post(
        "/api/campagne",
        json={
            "titolo": "Prima bozza",
            "inizio": inizio1.isoformat(),
            "fine": fine1.isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta1.status_code == 201

    inizio2 = fine1 + timedelta(days=5)
    fine2 = inizio2 + timedelta(days=10)
    risposta2 = client.post(
        "/api/campagne",
        json={
            "titolo": "Seconda bozza contemporanea",
            "inizio": inizio2.isoformat(),
            "fine": fine2.isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta2.status_code == 409
    assert "Esiste già una campagna in bozza" in risposta2.json()["detail"]


def test_ca12_periodo_sovrapposto_campagna_attiva_da_409(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-12: Campagna attiva sovrapposta dà 409; se respinta o scaduta -> ok."""
    u = utente_di_prova("artigiano")
    p = profilo(db, utente_id=u.id, canali=["instagram"])

    oggi = adesso().date()
    inizio_esistente = oggi + timedelta(days=10)
    fine_esistente = inizio_esistente + timedelta(days=20)

    c_attiva = campagna_in_bozza(
        db,
        profilo_id=p.id,
        titolo="Campagna già attiva",
        inizio=inizio_esistente,
        fine=fine_esistente,
        stato=domain.ATTIVA,
    )

    inizio_nuova = inizio_esistente + timedelta(days=5)
    fine_nuova = inizio_nuova + timedelta(days=10)

    risposta_sovrapposta = client.post(
        "/api/campagne",
        json={
            "titolo": "Bozza sovrapposta",
            "inizio": inizio_nuova.isoformat(),
            "fine": fine_nuova.isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta_sovrapposta.status_code == 409
    assert (
        "sovrappone a una campagna già esistente"
        in risposta_sovrapposta.json()["detail"]
    )

    c_attiva.stato = domain.RESPINTA
    db.flush()

    risposta_dopo_respinta = client.post(
        "/api/campagne",
        json={
            "titolo": "Bozza valida dopo respinta",
            "inizio": inizio_nuova.isoformat(),
            "fine": fine_nuova.isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta_dopo_respinta.status_code == 201


def test_ca48_creazione_canale_non_collegato_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-48: Canale senza account collegato alla creazione bozza dà 422."""
    u = utente_di_prova("artigiano")
    # Profilo con solo instagram collegato
    p = profilo(db, utente_id=u.id, canali=["instagram"])

    oggi = adesso().date()
    inizio = oggi + timedelta(days=5)
    fine = inizio + timedelta(days=15)

    # 1. Tentativo di creare bozza con 'facebook' che non è collegato -> 422
    risposta_fb = client.post(
        "/api/campagne",
        json={
            "titolo": "Campagna con FB non collegato",
            "inizio": inizio.isoformat(),
            "fine": fine.isoformat(),
            "canali": ["facebook"],
        },
    )
    assert risposta_fb.status_code == 422
    assert "non sono collegati" in risposta_fb.json()["detail"]

    # 2. Creazione con 'instagram' (collegato) -> 201
    risposta_ig = client.post(
        "/api/campagne",
        json={
            "titolo": "Campagna con IG collegato",
            "inizio": inizio.isoformat(),
            "fine": fine.isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta_ig.status_code == 201
    assert risposta_ig.json()["canali"] == ["instagram"]


def test_ca54_dettaglio_calcolo_post_chiesti_e_avvisi(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-54: Calcolo post_chiesti_per_canale e avvisi informativi (foto_poche, riempitivi_molti, frequenza_alta)."""
    u = utente_di_prova("artigiano")
    # Profilo con policy foto 'meno_5' e frequenza 'f3_4' (3 post/settimana)
    p = profilo(
        db,
        utente_id=u.id,
        canali=["instagram"],
        frequenza="f3_4",
        foto_policy={"quantita_mese": "meno_5"},
    )

    oggi = adesso().date()
    inizio = oggi + timedelta(days=5)
    # Durata di 14 giorni -> 3 post/settimana * 14 // 7 = 6 post chiesti
    fine = inizio + timedelta(days=13)

    c = campagna_in_bozza(
        db,
        profilo_id=p.id,
        titolo="Campagna con avvisi",
        inizio=inizio,
        fine=fine,
        canali=["instagram"],
    )
    # Nessuna foto caricata
    risposta_vuota = client.get(f"/api/campagne/{c.id}")
    assert risposta_vuota.status_code == 200
    dati = risposta_vuota.json()

    assert dati["post_chiesti_per_canale"] == {"instagram": 6}
    # Avvisi: foto caricate (0) < 6 -> foto_poche
    # foto caricate (0) -> riempitivi_molti (mancano 6)
    # frequenza f3_4 (3 post/sett) * 4 = 12 > 4 (limite meno_5) -> frequenza_alta
    avvisi = dati["avvisi"]
    assert "foto_poche" in avvisi
    assert "riempitivi_molti" in avvisi
    assert "frequenza_alta" in avvisi

    # Aggiungiamo un gruppo con 4 foto caricate:
    # post chiesti = 6, foto = 4 -> foto_poche resta (4 < 6)
    # mancanti = 2; 2 non supera 4 / 2 = 2 -> riempitivi_molti si spegne
    g = gruppo(db, campagna=c, origine="caricate")
    for _ in range(4):
        foto(db, gruppo=g)

    risposta_4foto = client.get(f"/api/campagne/{c.id}")
    assert risposta_4foto.status_code == 200
    avvisi_4 = risposta_4foto.json()["avvisi"]
    assert "foto_poche" in avvisi_4
    assert "riempitivi_molti" not in avvisi_4
    assert "frequenza_alta" in avvisi_4


def test_elenco_stati_multipli_e_dati_operatore(
    client: TestClient, utente_di_prova, db: Session
):
    """GET /campagne con stati ripetibili (?stato=bozza&stato=inviata) e arricchimento bottega/citta per l'operatore."""
    art = utente_di_prova("artigiano")
    p = profilo(db, utente_id=art.id, nome="Ceramiche del Corso", citta="Faenza")

    c_bozza = campagna_in_bozza(
        db, profilo_id=p.id, titolo="Bozza 1", stato=domain.BOZZA
    )
    c_inv = campagna_in_bozza(
        db, profilo_id=p.id, titolo="Inviata 1", stato=domain.INVIATA
    )
    c_att = campagna_in_bozza(
        db, profilo_id=p.id, titolo="Attiva 1", stato=domain.ATTIVA
    )

    # 1. Filtro stati multipli per l'artigiano: riceve solo bozza e inviata
    risposta_multi = client.get("/api/campagne?stato=bozza&stato=inviata")
    assert risposta_multi.status_code == 200
    ids_multi = [item["id"] for item in risposta_multi.json()]
    assert c_bozza.id in ids_multi
    assert c_inv.id in ids_multi
    assert c_att.id not in ids_multi
    # Per l'artigiano bottega e citta sono None
    assert risposta_multi.json()[0]["bottega"] is None
    assert risposta_multi.json()[0]["citta"] is None

    # 2. Per l'operatore: riceve bottega e citta valorizzate
    utente_di_prova("operatore")
    risposta_op = client.get("/api/campagne?stato=bozza&stato=inviata")
    assert risposta_op.status_code == 200
    trovata = next(item for item in risposta_op.json() if item["id"] == c_bozza.id)
    assert trovata["bottega"] == "Ceramiche del Corso"
    assert trovata["citta"] == "Faenza"


def test_creazione_richiede_ruolo_artigiano_da_403(client: TestClient, utente_di_prova):
    """Un operatore non può creare una campagna bozza (solo ruolo artigiano ammesso)."""
    utente_di_prova("operatore")
    oggi = adesso().date()
    risposta = client.post(
        "/api/campagne",
        json={
            "titolo": "Campagna operatore illegale",
            "inizio": (oggi + timedelta(days=5)).isoformat(),
            "fine": (oggi + timedelta(days=15)).isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta.status_code == 403


def test_debug_date_limite_esatto_3_giorni_e_92_giorni_consentite(
    client: TestClient, utente_di_prova, db: Session
):
    """Caso limite: inizio esattamente tra 3 giorni e durata esattamente di 92 giorni sono ammesse."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id, canali=["instagram"])

    oggi = adesso().astimezone(ROMA).date()
    inizio_esatto = oggi + timedelta(days=3)
    fine_esatta = inizio_esatto + timedelta(days=91)  # 92 giorni inclusi

    risposta = client.post(
        "/api/campagne",
        json={
            "titolo": "Campagna con limiti esatti",
            "inizio": inizio_esatto.isoformat(),
            "fine": fine_esatta.isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta.status_code == 201
    assert risposta.json()["inizio"] == inizio_esatto.isoformat()
    assert risposta.json()["fine"] == fine_esatta.isoformat()


def test_debug_artigiano_senza_profilo_gestito_con_grazia(
    client: TestClient, utente_di_prova
):
    """Un utente artigiano che non ha ancora compilato il profilo non deve causare 500."""
    utente_di_prova("artigiano")
    oggi = adesso().date()

    risposta_post = client.post(
        "/api/campagne",
        json={
            "titolo": "Senza bottega",
            "inizio": (oggi + timedelta(days=5)).isoformat(),
            "fine": (oggi + timedelta(days=15)).isoformat(),
            "canali": ["instagram"],
        },
    )
    assert risposta_post.status_code == 422
    assert "Profilo bottega non trovato" in risposta_post.json()["detail"]

    risposta_get = client.get("/api/campagne")
    assert risposta_get.status_code == 200
    assert risposta_get.json() == []

    risposta_id = client.get("/api/campagne/12345")
    assert risposta_id.status_code == 404


def test_debug_creazione_bozza_concorrente_atomica(motore_test):
    """Verifica che chiamate concorrenti sullo stesso artigiano non creino bozze duplicate."""
    import concurrent.futures
    from sqlalchemy import text
    from sqlalchemy.orm import Session as SessionClass

    from app.core.errori import StatoNonValido
    from app.moduli.campagne.schemas import CampagnaCrea
    from app.moduli.campagne.service import crea_bozza

    with SessionClass(motore_test) as s, s.begin():
        p = profilo(s, canali=["instagram"])
        u_id = p.utente_id
        profilo_id = p.id

    try:
        dati = CampagnaCrea(
            titolo="Bozza concorrente",
            inizio=adesso().date() + timedelta(days=5),
            fine=adesso().date() + timedelta(days=15),
            canali=["instagram"],
        )
        ora = adesso()

        def tenta_creazione():
            with SessionClass(motore_test) as sessione:
                try:
                    with sessione.begin():
                        crea_bozza(sessione, u_id, dati, ora)
                    return "ok"
                except StatoNonValido:
                    return "409"

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(tenta_creazione) for _ in range(4)]
            esiti = [f.result() for f in futures]

        assert esiti.count("ok") == 1
        assert esiti.count("409") == 3
    finally:
        with SessionClass(motore_test) as s, s.begin():
            s.execute(
                text("DELETE FROM campagna WHERE profilo_id = :pid"),
                {"pid": profilo_id},
            )
            s.execute(
                text("DELETE FROM account_social WHERE profilo_id = :pid"),
                {"pid": profilo_id},
            )
            s.execute(
                text("DELETE FROM profilo_bottega WHERE id = :pid"),
                {"pid": profilo_id},
            )
            s.execute(text("DELETE FROM utente WHERE id = :uid"), {"uid": u_id})


def test_debug_canali_case_insensitive_e_spazi(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che i canali forniti con maiuscole e spazi vengano puliti e accettati."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id, canali=["instagram", "facebook"])

    oggi = adesso().astimezone(ROMA).date()
    inizio = oggi + timedelta(days=5)
    fine = inizio + timedelta(days=10)

    res = client.post(
        "/api/campagne",
        json={
            "titolo": "Campagna con canali misti",
            "inizio": inizio.isoformat(),
            "fine": fine.isoformat(),
            "canali": ["  Instagram  ", "FACEBOOK"],
        },
    )
    assert res.status_code == 201
    assert res.json()["canali"] == ["instagram", "facebook"]


def test_debug_foto_policy_come_stringa_json_in_dettaglio(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica che se foto_policy è serializzata come stringa JSON, venga gestita senza 500."""
    from sqlalchemy import text

    u = utente_di_prova("artigiano")
    p = profilo(
        db,
        utente_id=u.id,
        canali=["instagram"],
        frequenza="f3_4",
    )
    # Aggiorna foto_policy come stringa json raw nel DB
    db.execute(
        text("UPDATE profilo_bottega SET foto_policy = :fp WHERE id = :pid"),
        {"fp": '{"quantita_mese": "meno_5"}', "pid": p.id},
    )
    db.flush()

    oggi = adesso().astimezone(ROMA).date()
    c = campagna_in_bozza(
        db,
        profilo_id=p.id,
        inizio=oggi + timedelta(days=5),
        fine=oggi + timedelta(days=18),
        canali=["instagram"],
    )

    res = client.get(f"/api/campagne/{c.id}")
    assert res.status_code == 200
    assert "frequenza_alta" in res.json()["avvisi"]


def test_debug_durata_minima_7_giorni_esatta(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica il confine esatto: durata 7 giorni esatti consentita, 6 giorni da 422."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id, canali=["instagram"])

    oggi = adesso().astimezone(ROMA).date()
    inizio = oggi + timedelta(days=5)

    # 6 giorni (es. inizio + 5 giorni inclusi) -> 422
    res_6g = client.post(
        "/api/campagne",
        json={
            "titolo": "Durata 6 giorni",
            "inizio": inizio.isoformat(),
            "fine": (inizio + timedelta(days=5)).isoformat(),
            "canali": ["instagram"],
        },
    )
    assert res_6g.status_code == 422
    assert "almeno 7 giorni" in res_6g.json()["detail"]

    # 7 giorni (inizio + 6 giorni inclusi) -> 201
    res_7g = client.post(
        "/api/campagne",
        json={
            "titolo": "Durata 7 giorni esatti",
            "inizio": inizio.isoformat(),
            "fine": (inizio + timedelta(days=6)).isoformat(),
            "canali": ["instagram"],
        },
    )
    assert res_7g.status_code == 201
    assert res_7g.json()["titolo"] == "Durata 7 giorni esatti"
