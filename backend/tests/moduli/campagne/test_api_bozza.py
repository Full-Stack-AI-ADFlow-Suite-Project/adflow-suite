"""Test per le API di creazione, elenco e dettaglio delle campagne (T1-22).

Verifica i criteri di accettazione:
- CA-04: artigiano accede a campagna o foto altrui -> 404 (non 403)
- CA-09: inizio < oggi + 3 giorni -> 422
- CA-10: durata > 92 giorni o fine <= inizio -> 422
- CA-11: bozza esistente per lo stesso artigiano -> 409
- CA-12: periodo sovrapposto con campagna attiva/in corso -> 409; se respinta o scaduta -> ok
- CA-46: crea_immagini_ai salvato e restituito nel dettaglio
- Ruoli e permessi: POST riservato ad artigiano (403 ad altri ruoli).
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.core.orologio import adesso
from app.moduli.campagne import domain
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_in_bozza


def test_ca04_artigiano_accede_a_campagna_altrui_da_404(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-04: L'artigiano che tenta di consultare una campagna altrui riceve 404."""
    # 1. L'artigiano proprietario consulta la propria campagna con successo (200)
    artigiano_a = utente_di_prova("artigiano")
    profilo_a = profilo(db, utente_id=artigiano_a.id)
    c_a = campagna_in_bozza(db, profilo_id=profilo_a.id, titolo="Campagna A")

    risposta_proprietario = client.get(f"/api/campagne/{c_a.id}")
    assert risposta_proprietario.status_code == 200
    assert risposta_proprietario.json()["id"] == c_a.id
    assert risposta_proprietario.json()["titolo"] == "Campagna A"

    # 2. Entra l'artigiano B: se richiede la campagna di A riceve 404 (anti-disclosure)
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
    profilo(db, utente_id=u.id)

    oggi = adesso().date()
    # 2 giorni di anticipo (minimo richiesto: 3 giorni)
    inizio_non_valido = oggi + timedelta(days=2)
    fine = inizio_non_valido + timedelta(days=10)

    payload = {
        "titolo": "Campagna troppo anticipata",
        "inizio": inizio_non_valido.isoformat(),
        "fine": fine.isoformat(),
        "descrizione": "Descrizione di prova",
    }
    risposta = client.post("/api/campagne", json=payload)
    assert risposta.status_code == 422
    assert "almeno 3 giorni" in risposta.json()["detail"]


def test_ca10_durata_superiore_92_giorni_o_fine_prima_inizio_da_422(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-10: Durata > 92 giorni o fine <= inizio deve fallire con 422."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id)

    oggi = adesso().date()
    inizio_valido = oggi + timedelta(days=5)

    # 1. Fine precedente a inizio
    risposta_fine_precedente = client.post(
        "/api/campagne",
        json={
            "titolo": "Date invertite",
            "inizio": inizio_valido.isoformat(),
            "fine": (inizio_valido - timedelta(days=1)).isoformat(),
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
        },
    )
    assert risposta_fine_uguale.status_code == 422

    # 3. Durata superiore a 92 giorni (es. 93 giorni)
    risposta_troppo_lunga = client.post(
        "/api/campagne",
        json={
            "titolo": "Troppo lunga",
            "inizio": inizio_valido.isoformat(),
            "fine": (inizio_valido + timedelta(days=93)).isoformat(),
        },
    )
    assert risposta_troppo_lunga.status_code == 422
    assert "superare 92 giorni" in risposta_troppo_lunga.json()["detail"]


def test_ca11_bozza_esistente_nuova_bozza_da_409(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-11: Se l'artigiano ha già una bozza aperta, un'altra bozza dà 409."""
    u = utente_di_prova("artigiano")
    p = profilo(db, utente_id=u.id)

    oggi = adesso().date()
    inizio1 = oggi + timedelta(days=5)
    fine1 = inizio1 + timedelta(days=10)

    # Creazione della prima bozza con successo (201)
    risposta1 = client.post(
        "/api/campagne",
        json={
            "titolo": "Prima bozza",
            "inizio": inizio1.isoformat(),
            "fine": fine1.isoformat(),
        },
    )
    assert risposta1.status_code == 201

    # Tentativo di creare una seconda bozza: deve fallire con 409
    inizio2 = fine1 + timedelta(days=5)
    fine2 = inizio2 + timedelta(days=10)
    risposta2 = client.post(
        "/api/campagne",
        json={
            "titolo": "Seconda bozza contemporanea",
            "inizio": inizio2.isoformat(),
            "fine": fine2.isoformat(),
        },
    )
    assert risposta2.status_code == 409
    assert "Esiste già una campagna in bozza" in risposta2.json()["detail"]


def test_ca12_periodo_sovrapposto_campagna_attiva_da_409(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-12: Campagna attiva sovrapposta dà 409; se respinta o scaduta -> ok."""
    u = utente_di_prova("artigiano")
    p = profilo(db, utente_id=u.id)

    oggi = adesso().date()
    inizio_esistente = oggi + timedelta(days=10)
    fine_esistente = inizio_esistente + timedelta(days=20)

    # 1. Con campagna nello stato 'attiva'
    c_attiva = campagna_in_bozza(
        db,
        profilo_id=p.id,
        titolo="Campagna già attiva",
        inizio=inizio_esistente,
        fine=fine_esistente,
        stato=domain.ATTIVA,
    )

    # Tentativo di creare bozza con periodo sovrapposto
    inizio_nuova = inizio_esistente + timedelta(days=5)
    fine_nuova = inizio_nuova + timedelta(days=10)

    risposta_sovrapposta = client.post(
        "/api/campagne",
        json={
            "titolo": "Bozza sovrapposta",
            "inizio": inizio_nuova.isoformat(),
            "fine": fine_nuova.isoformat(),
        },
    )
    assert risposta_sovrapposta.status_code == 409
    assert (
        "sovrappone a una campagna già esistente"
        in risposta_sovrapposta.json()["detail"]
    )

    # 2. Se la campagna precedente passa a 'respinta' o 'scaduta', la nuova bozza è ammessa
    c_attiva.stato = domain.RESPINTA
    db.flush()

    risposta_dopo_respinta = client.post(
        "/api/campagne",
        json={
            "titolo": "Bozza valida dopo respinta",
            "inizio": inizio_nuova.isoformat(),
            "fine": fine_nuova.isoformat(),
        },
    )
    assert risposta_dopo_respinta.status_code == 201


def test_ca46_crea_immagini_ai_salvato_e_restituito(
    client: TestClient, utente_di_prova, db: Session
):
    """CA-46: Il flag crea_immagini_ai viene salvato e restituito nel dettaglio."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id)

    oggi = adesso().date()
    inizio = oggi + timedelta(days=4)
    fine = inizio + timedelta(days=14)

    # Creazione con crea_immagini_ai = True
    risposta_crea = client.post(
        "/api/campagne",
        json={
            "titolo": "Campagna con AI",
            "inizio": inizio.isoformat(),
            "fine": fine.isoformat(),
            "crea_immagini_ai": True,
        },
    )
    assert risposta_crea.status_code == 201
    dati = risposta_crea.json()
    assert dati["crea_immagini_ai"] is True
    campagna_id = dati["id"]

    # Lettura dettaglio via GET
    risposta_get = client.get(f"/api/campagne/{campagna_id}")
    assert risposta_get.status_code == 200
    assert risposta_get.json()["crea_immagini_ai"] is True


def test_elenco_campagne_artigiano_e_operatore(
    client: TestClient, utente_di_prova, db: Session
):
    """L'artigiano visualizza solo le sue campagne, l'operatore tutte."""
    artigiano_1 = utente_di_prova("artigiano")
    profilo_1 = profilo(db, utente_id=artigiano_1.id)
    c1 = campagna_in_bozza(db, profilo_id=profilo_1.id, titolo="Campagna 1")

    artigiano_2 = utente_di_prova("artigiano")
    profilo_2 = profilo(db, utente_id=artigiano_2.id)
    c2 = campagna_in_bozza(db, profilo_id=profilo_2.id, titolo="Campagna 2")

    # Artigiano 2 vede solo la propria campagna
    risposta_art2 = client.get("/api/campagne")
    assert risposta_art2.status_code == 200
    id_art2 = [item["id"] for item in risposta_art2.json()]
    assert c2.id in id_art2
    assert c1.id not in id_art2

    # Operatore vede tutte le campagne
    utente_di_prova("operatore")
    risposta_op = client.get("/api/campagne")
    assert risposta_op.status_code == 200
    id_op = [item["id"] for item in risposta_op.json()]
    assert c1.id in id_op
    assert c2.id in id_op


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
        },
    )
    assert risposta.status_code == 403


def test_debug_date_limite_esatto_3_giorni_e_92_giorni_consentite(
    client: TestClient, utente_di_prova, db: Session
):
    """Caso limite: inizio esattamente tra 3 giorni e durata esattamente di 92 giorni sono ammesse."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id)

    oggi = adesso().date()
    inizio_esatto = oggi + timedelta(days=3)
    fine_esatta = inizio_esatto + timedelta(days=92)

    risposta = client.post(
        "/api/campagne",
        json={
            "titolo": "Campagna con limiti esatti",
            "inizio": inizio_esatto.isoformat(),
            "fine": fine_esatta.isoformat(),
        },
    )
    assert risposta.status_code == 201
    assert risposta.json()["inizio"] == inizio_esatto.isoformat()
    assert risposta.json()["fine"] == fine_esatta.isoformat()


def test_debug_sovrapposizioni_limiti_precisi(
    client: TestClient, utente_di_prova, db: Session
):
    """Verifica millimetrica dei confini di sovrapposizione temporale."""
    u = utente_di_prova("artigiano")
    p = profilo(db, utente_id=u.id)

    oggi = adesso().date()
    # Campagna attiva di riferimento: [giorno 10, giorno 20]
    inizio_rif = oggi + timedelta(days=10)
    fine_rif = inizio_rif + timedelta(days=10)

    c_attiva = campagna_in_bozza(
        db,
        profilo_id=p.id,
        titolo="Campagna centrale attiva",
        inizio=inizio_rif,
        fine=fine_rif,
        stato=domain.ATTIVA,
    )

    # 1. Periodo precedente adiacente [giorno 3, giorno 9] -> non si sovrappone, ok
    risposta_pre = client.post(
        "/api/campagne",
        json={
            "titolo": "Precedente adiacente",
            "inizio": (oggi + timedelta(days=3)).isoformat(),
            "fine": (inizio_rif - timedelta(days=1)).isoformat(),
        },
    )
    assert risposta_pre.status_code == 201

    # Rimuoviamo la bozza per continuare i test di sovrapposizione
    db.delete(db.get(c_attiva.__class__, risposta_pre.json()["id"]))
    db.flush()

    # 2. Periodo che tocca l'estremo superiore del giorno 20 [giorno 20, giorno 25] -> tocca il 20, sovrapposto (409)
    risposta_tocca_fine = client.post(
        "/api/campagne",
        json={
            "titolo": "Tocca il giorno finale",
            "inizio": fine_rif.isoformat(),
            "fine": (fine_rif + timedelta(days=5)).isoformat(),
        },
    )
    assert risposta_tocca_fine.status_code == 409

    # 3. Periodo successivo adiacente [giorno 21, giorno 30] -> non si sovrappone, ok
    risposta_post = client.post(
        "/api/campagne",
        json={
            "titolo": "Successiva adiacente",
            "inizio": (fine_rif + timedelta(days=1)).isoformat(),
            "fine": (fine_rif + timedelta(days=10)).isoformat(),
        },
    )
    assert risposta_post.status_code == 201


def test_debug_artigiano_senza_profilo_gestito_con_grazia(
    client: TestClient, utente_di_prova
):
    """Un utente artigiano che non ha ancora compilato il profilo non deve causare 500."""
    utente_di_prova("artigiano")
    oggi = adesso().date()

    # POST crea bozza -> 422 con spiegazione
    risposta_post = client.post(
        "/api/campagne",
        json={
            "titolo": "Senza bottega",
            "inizio": (oggi + timedelta(days=5)).isoformat(),
            "fine": (oggi + timedelta(days=15)).isoformat(),
        },
    )
    assert risposta_post.status_code == 422
    assert "Profilo bottega non trovato" in risposta_post.json()["detail"]

    # GET elenco -> lista vuota 200
    risposta_get = client.get("/api/campagne")
    assert risposta_get.status_code == 200
    assert risposta_get.json() == []

    # GET dettaglio id inventato -> 404
    risposta_id = client.get("/api/campagne/12345")
    assert risposta_id.status_code == 404


def test_debug_validazione_difensiva_stringhe(
    client: TestClient, utente_di_prova, db: Session
):
    """Defense in Depth: blocco stringhe vuote, NUL byte e payload sovradimensionati."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id)

    oggi = adesso().date()
    inizio = oggi + timedelta(days=5)
    fine = inizio + timedelta(days=10)

    # Titolo solo spazi
    assert (
        client.post(
            "/api/campagne",
            json={
                "titolo": "   ",
                "inizio": inizio.isoformat(),
                "fine": fine.isoformat(),
            },
        ).status_code
        == 422
    )

    # Titolo con byte NUL
    assert (
        client.post(
            "/api/campagne",
            json={
                "titolo": "Titolo\x00Invalido",
                "inizio": inizio.isoformat(),
                "fine": fine.isoformat(),
            },
        ).status_code
        == 422
    )

    # Descrizione con byte NUL
    assert (
        client.post(
            "/api/campagne",
            json={
                "titolo": "Titolo ok",
                "inizio": inizio.isoformat(),
                "fine": fine.isoformat(),
                "descrizione": "Descrizione\x00NonValida",
            },
        ).status_code
        == 422
    )

    # Titolo > 200 caratteri
    assert (
        client.post(
            "/api/campagne",
            json={
                "titolo": "A" * 201,
                "inizio": inizio.isoformat(),
                "fine": fine.isoformat(),
            },
        ).status_code
        == 422
    )

    # Descrizione > 2000 caratteri
    assert (
        client.post(
            "/api/campagne",
            json={
                "titolo": "Titolo ok",
                "inizio": inizio.isoformat(),
                "fine": fine.isoformat(),
                "descrizione": "D" * 2001,
            },
        ).status_code
        == 422
    )


def test_debug_riservatezza_operatore_vs_artigiano_nel_dettaglio(
    client: TestClient, utente_di_prova, db: Session
):
    """Nel dettaglio: l'operatore vede snapshot e decisioni; l'artigiano solo i propri dati."""
    art = utente_di_prova("artigiano")
    p = profilo(db, utente_id=art.id)
    c = campagna_in_bozza(db, profilo_id=p.id, titolo="Campagna Dettaglio")

    # Artigiano legge il dettaglio: non deve vedere profilo_snapshot o decisioni altrui
    risposta_art = client.get(f"/api/campagne/{c.id}")
    assert risposta_art.status_code == 200
    assert risposta_art.json()["profilo_snapshot"] is None
    assert risposta_art.json()["decisioni"] == []

    # Operatore legge il dettaglio: campi snapshot e decisioni sono accessibili
    utente_di_prova("operatore")
    risposta_op = client.get(f"/api/campagne/{c.id}")
    assert risposta_op.status_code == 200
    assert "profilo_snapshot" in risposta_op.json()
    assert "decisioni" in risposta_op.json()


def test_debug_filtro_stato_valido_ed_errore_su_stato_sconosciuto(
    client: TestClient, utente_di_prova, db: Session
):
    """Il filtro ?stato= accetta stati validi e rigetta con 422 stati inventati."""
    u = utente_di_prova("artigiano")
    p = profilo(db, utente_id=u.id)
    campagna_in_bozza(db, profilo_id=p.id, stato=domain.BOZZA)

    # 1. Filtro valido
    risposta_ok = client.get("/api/campagne?stato=bozza")
    assert risposta_ok.status_code == 200
    assert len(risposta_ok.json()) == 1

    # 2. Filtro con stato sconosciuto -> 422
    risposta_err = client.get("/api/campagne?stato=inesistente")
    assert risposta_err.status_code == 422
    assert "non valido" in risposta_err.json()["detail"]

    # 3. Filtro vuoto ?stato= -> trattato come assenza di filtro, 200
    risposta_vuoto = client.get("/api/campagne?stato=")
    assert risposta_vuoto.status_code == 200
    assert len(risposta_vuoto.json()) == 1


def test_debug_descrizione_spazi_normalizzata_a_none(
    client: TestClient, utente_di_prova, db: Session
):
    """Una descrizione composta da soli spazi viene ripulita e memorizzata come None."""
    u = utente_di_prova("artigiano")
    profilo(db, utente_id=u.id)

    oggi = adesso().date()
    risposta = client.post(
        "/api/campagne",
        json={
            "titolo": "Campagna con descrizione a spazi",
            "inizio": (oggi + timedelta(days=5)).isoformat(),
            "fine": (oggi + timedelta(days=15)).isoformat(),
            "descrizione": "     ",
        },
    )
    assert risposta.status_code == 201
    assert risposta.json()["descrizione"] is None


def test_debug_ruolo_non_previsto_riceve_403(
    client: TestClient, utente_di_prova, db: Session
):
    """Un ruolo anomalo o non previsto non può visualizzare campagne."""
    utente_di_prova("artigiano")
    p = profilo(db)
    c = campagna_in_bozza(db, profilo_id=p.id)

    utente_ospite = utente_di_prova("ospite")
    risposta = client.get(f"/api/campagne/{c.id}")
    assert risposta.status_code == 403


def test_debug_creazione_bozza_concorrente_atomica(motore_test):
    """Verifica che chiamate concorrenti sullo stesso artigiano non creino bozze duplicate."""
    import concurrent.futures
    from sqlalchemy import text
    from sqlalchemy.orm import Session as SessionClass
    from app.moduli.campagne.service import crea_bozza
    from app.moduli.campagne.schemas import CampagnaCrea
    from app.core.errori import StatoNonValido

    with SessionClass(motore_test) as s, s.begin():
        p = profilo(s)
        u_id = p.utente_id
        profilo_id = p.id

    try:
        dati = CampagnaCrea(
            titolo="Bozza concorrente",
            inizio=adesso().date() + timedelta(days=5),
            fine=adesso().date() + timedelta(days=15),
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

        # Esattamente una deve aver avuto successo (ok) e tutte le altre 3 devono aver ricevuto 409
        assert esiti.count("ok") == 1
        assert esiti.count("409") == 3
    finally:
        # Cleanup deterministico per non inquinare il DB negli altri test
        with SessionClass(motore_test) as s, s.begin():
            s.execute(
                text("DELETE FROM campagna WHERE profilo_id = :pid"),
                {"pid": profilo_id},
            )
            s.execute(
                text("DELETE FROM profilo_bottega WHERE id = :pid"), {"pid": profilo_id}
            )
            s.execute(text("DELETE FROM utente WHERE id = :uid"), {"uid": u_id})
