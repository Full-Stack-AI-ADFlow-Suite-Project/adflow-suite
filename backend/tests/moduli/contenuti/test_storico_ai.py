"""T3-917: lo storico dell'AI in lettura (spec R-50, CA-110, CA-111)."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.moduli.contenuti.models import ValutazioneAI, VersionePost
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import (
    chiamata_ai,
    post_approvato,
    post_da_approvare,
    valutazione_ai,
)


def _alle(giorno: int, ora: int = 12) -> datetime:
    return datetime(2030, 1, giorno, ora, tzinfo=timezone.utc)


def _ids(risposta) -> list[int]:
    return [voce["id"] for voce in risposta.json()["voci"]]


def test_ca110_i_filtri_danno_solo_le_righe_giuste_dalla_piu_recente(
    db, client, utente_di_prova
):
    utente_di_prova("operatore")
    uno, due = campagna_in_revisione(db), campagna_in_revisione(db)
    a = chiamata_ai(db, uno, tipo="piano", creata_il=_alle(5))
    b = chiamata_ai(db, uno, tipo="testo", creata_il=_alle(6), modello_ai="gpt-x")
    c = chiamata_ai(
        db, due, tipo="testo", creata_il=_alle(7), esito="temporaneo", errore="x"
    )
    d = chiamata_ai(db, due, tipo="testo", creata_il=_alle(8), versione_prompt="v3")
    db.commit()

    tutte = client.get("/api/storico-ai")
    assert tutte.status_code == 200
    assert _ids(tutte) == [d.id, c.id, b.id, a.id]
    assert (tutte.json()["totale"], tutte.json()["pagina"]) == (4, 1)
    assert tutte.json()["per_pagina"] == 50

    def con(**filtri) -> list[int]:
        return _ids(client.get("/api/storico-ai", params=filtri))

    assert con(campagna_id=uno.id) == [b.id, a.id]
    assert con(tipo="piano") == [a.id]
    assert con(modello="gpt-x") == [b.id]
    assert con(versione_prompt="v3") == [d.id]
    assert con(esito="temporaneo") == [c.id]
    assert con(dal="2030-01-06", al="2030-01-07") == [c.id, b.id]
    riga = client.get("/api/storico-ai", params={"campagna_id": due.id}).json()["voci"][
        0
    ]
    assert riga["campagna_titolo"]
    assert riga["bottega"]


def test_ca110_dal_e_al_sono_giorni_di_roma_compresi(db, client, utente_di_prova):
    utente_di_prova("operatore")
    # 23:30 UTC del 5 gennaio sono le 00:30 del 6 a Roma.
    tardi = chiamata_ai(db, creata_il=_alle(5, 23).replace(minute=30))
    db.commit()

    assert _ids(client.get("/api/storico-ai", params={"al": "2030-01-05"})) == []
    assert _ids(client.get("/api/storico-ai", params={"dal": "2030-01-06"})) == [
        tardi.id
    ]
    assert _ids(client.get("/api/storico-ai", params={"al": "2030-01-06"})) == [
        tardi.id
    ]


def test_ca110_cinquanta_per_pagina(db, client, utente_di_prova):
    utente_di_prova("operatore")
    campagna = campagna_in_revisione(db)
    righe = [chiamata_ai(db, campagna, creata_il=_alle(5, 8)) for _ in range(51)]
    db.commit()

    prima = client.get("/api/storico-ai").json()
    seconda = client.get("/api/storico-ai", params={"pagina": 2}).json()
    assert (len(prima["voci"]), prima["totale"]) == (50, 51)
    assert [v["id"] for v in seconda["voci"]] == [righe[0].id]
    assert client.get("/api/storico-ai", params={"pagina": 0}).status_code == 422


def test_ca110_il_dettaglio_ha_richiesta_risposta_e_valutazioni(
    db, client, utente_di_prova
):
    operatore = utente_di_prova("operatore", nome="Marta Rossi")
    chiamata = chiamata_ai(
        db,
        tipo="piano",
        richiesta={"foto": ["<foto 3>"]},
        risposta='{"strategia": "x"}',
        tentativo=2,
        durata_ms=900,
        token_ingresso=10,
    )
    valutazione_ai(db, chiamata, operatore, 4, nota="Buono")
    db.commit()

    risposta = client.get(f"/api/storico-ai/{chiamata.id}")
    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["richiesta"] == {"foto": ["<foto 3>"]}
    assert (corpo["risposta"], corpo["tentativo"]) == ('{"strategia": "x"}', 2)
    assert corpo["voto_medio"] == 4
    (voto,) = corpo["valutazioni"]
    assert (voto["utente_nome"], voto["voto"], voto["nota"]) == (
        "Marta Rossi",
        4,
        "Buono",
    )

    mancante = client.get("/api/storico-ai/999999")
    assert mancante.status_code == 404
    assert mancante.json() == {"detail": "Chiamata non trovata."}


def test_ca110_l_artigiano_non_entra_e_l_admin_si(db, client, utente_di_prova):
    chiamata = chiamata_ai(db)
    db.commit()
    for percorso in (
        "/api/storico-ai",
        "/api/storico-ai/numeri",
        f"/api/storico-ai/{chiamata.id}",
    ):
        utente_di_prova("artigiano")
        assert client.get(percorso).status_code == 403
    utente_di_prova("admin")
    assert client.get("/api/storico-ai").status_code == 200
    assert client.get("/api/storico-ai/numeri").status_code == 200


def _versione(post, numero: int, tipo: str, **campi) -> VersionePost:
    return VersionePost(
        post_id=post.id,
        numero=numero,
        testo="Testo",
        hashtag=[],
        tipo_intervento=tipo,
        **campi,
    )


def test_ca111_i_numeri_di_una_campagna(db, client, utente_di_prova):
    utente_di_prova("operatore")
    campagna = campagna_in_revisione(db)
    chiamata_ai(db, campagna, tipo="piano", versione_prompt="v2", durata_ms=1000)
    chiamata_ai(
        db,
        campagna,
        tipo="testo",
        versione_prompt="v3",
        durata_ms=2000,
        costo_usd=Decimal("0.5"),
    )
    chiamata_ai(
        db,
        campagna,
        tipo="testo",
        versione_prompt="v3",
        durata_ms=None,
        esito="risposta",
        errore="risposta: x",
    )
    chiamata_ai(
        db,
        campagna,
        tipo="immagine",
        versione_prompt="img-1",
        durata_ms=3000,
        n_immagini=1,
    )
    votata = chiamata_ai(db, campagna, tipo="testo", versione_prompt="v3")
    valutazione_ai(db, votata, utente_di_prova("operatore"), 5)
    valutazione_ai(db, votata, utente_di_prova("operatore"), 3)

    # Quattro post approvati: uno com'era scritto, uno modificato a mano, uno
    # rigenerato, uno con l'immagine rigenerata; un quinto da approvare.
    come_scritto = post_approvato(db, campagna_id=campagna.id, canale="facebook")
    a_mano = post_approvato(db, campagna_id=campagna.id, canale="instagram")
    db.add(_versione(a_mano, 2, "modifica_operatore"))
    rigenerato = post_approvato(db, campagna_id=campagna.id)
    db.add(_versione(rigenerato, 2, "rigenera_totale"))
    con_immagine = post_approvato(db, campagna_id=campagna.id)
    db.add(_versione(con_immagine, 2, "rigenera_immagine"))
    senza_immagine = post_da_approvare(db, campagna_id=campagna.id)
    db.add(
        _versione(
            senza_immagine,
            2,
            "rigenera_totale",
            errori_validazione=[
                {"livello": "blocco", "regola": "immagine_non_creata", "messaggio": "x"}
            ],
        )
    )
    db.add(
        _versione(
            senza_immagine,
            3,
            "rigenera_da_proposta",
            errori_validazione=[
                {"livello": "blocco", "regola": "immagine_non_creata", "messaggio": "x"}
            ],
        )
    )
    db.commit()
    assert come_scritto.id

    risposta = client.get("/api/storico-ai/numeri", params={"campagna_id": campagna.id})
    assert risposta.status_code == 200
    n = risposta.json()
    assert n["chiamate"] == 5
    assert Decimal(n["costo_usd"]) == Decimal("0.5")
    assert n["durata_media_ms"] == 2000  # (1000 + 2000 + 3000) / 3, il nullo escluso
    assert n["tasso_errore"] == 0.2
    assert n["voto_medio"] == 4
    assert n["testi_approvati"] == 4
    assert n["testi_approvati_come_ai"] == 3  # tutti tranne quello modificato a mano
    assert n["modifiche_a_mano"] == 1
    assert n["rigenerazioni_testo"] == 3
    assert n["immagini_create"] == 1
    assert n["immagini_non_create"] == 1
    assert n["immagini_rigenerate"] == 1

    per_versione = {(r["tipo"], r["versione_prompt"]): r for r in n["per_versione"]}
    assert [(r["tipo"], r["versione_prompt"]) for r in n["per_versione"]] == [
        ("piano", "v2"),
        ("testo", "v3"),
        ("immagine", "img-1"),
    ]
    testo = per_versione[("testo", "v3")]
    assert testo["chiamate"] == 3
    assert abs(testo["tasso_errore"] - 1 / 3) < 1e-9
    assert testo["durata_media_ms"] == 2000
    assert testo["voto_medio"] == 4


def test_ca111_senza_chiamate_i_numeri_sono_zero(db, client, utente_di_prova):
    utente_di_prova("operatore")
    n = client.get("/api/storico-ai/numeri").json()
    assert n["chiamate"] == 0 and n["tasso_errore"] == 0
    assert n["durata_media_ms"] is None and n["durata_p95_ms"] is None
    assert n["per_versione"] == []


def test_ca111_il_p95_e_la_media_usano_le_sole_durate_non_nulle(
    db, client, utente_di_prova
):
    utente_di_prova("operatore")
    campagna = campagna_in_revisione(db)
    for durata in range(100, 2100, 100):  # 20 durate: 100 … 2000
        chiamata_ai(db, campagna, durata_ms=durata)
    chiamata_ai(db, campagna, durata_ms=None)

    n = client.get("/api/storico-ai/numeri").json()
    assert n["chiamate"] == 21
    assert n["durata_media_ms"] == 1050
    assert n["durata_p95_ms"] == 1900


# --- Voto (T3-918, CA-112) ----------------------------------------------------


def test_ca112_un_voto_con_nota_resta_con_l_operatore_e_un_secondo_non_cancella_il_primo(
    db, client, utente_di_prova
):
    marta = utente_di_prova("operatore", nome="Marta Rossi")
    chiamata = chiamata_ai(db)
    db.commit()

    primo = client.post(
        f"/api/storico-ai/{chiamata.id}/voto", json={"voto": 4, "nota": "Buono"}
    )
    assert primo.status_code == 200
    assert (primo.json()["utente_nome"], primo.json()["voto"]) == ("Marta Rossi", 4)
    assert primo.json()["nota"] == "Buono"

    luca = utente_di_prova("operatore", nome="Luca Verdi")
    secondo = client.post(f"/api/storico-ai/{chiamata.id}/voto", json={"voto": 2})
    assert secondo.status_code == 200 and secondo.json()["nota"] is None
    # anche la stessa persona può votare ancora: il voto di prima resta
    terzo = client.post(f"/api/storico-ai/{chiamata.id}/voto", json={"voto": 5})
    assert terzo.status_code == 200

    righe = db.scalars(
        select(ValutazioneAI)
        .where(ValutazioneAI.chiamata_ai_id == chiamata.id)
        .order_by(ValutazioneAI.id)
    ).all()
    assert [(r.utente_id, r.voto) for r in righe] == [
        (marta.id, 4),
        (luca.id, 2),
        (luca.id, 5),
    ]

    elenco = client.get("/api/storico-ai").json()["voci"][0]
    assert elenco["voto_medio"] == round((4 + 2 + 5) / 3, 2)
    dettaglio = client.get(f"/api/storico-ai/{chiamata.id}").json()
    assert [v["voto"] for v in dettaglio["valutazioni"]] == [4, 2, 5]


def test_ca112_voto_fuori_da_1_a_5_o_campi_in_piu_sono_422(db, client, utente_di_prova):
    utente_di_prova("operatore")
    chiamata = chiamata_ai(db)
    db.commit()
    url = f"/api/storico-ai/{chiamata.id}/voto"

    for corpo in (
        {"voto": 0},
        {"voto": 6},
        {"voto": "alto"},
        {},
        {"voto": 3, "nota": "x" * 1001},
        {"voto": 3, "altro": 1},
    ):
        assert client.post(url, json=corpo).status_code == 422, corpo
    assert db.scalar(select(func.count()).select_from(ValutazioneAI)) == 0


def test_ca112_chiamata_che_non_c_e_404_e_artigiano_403(db, client, utente_di_prova):
    utente_di_prova("operatore")
    mancante = client.post("/api/storico-ai/999999/voto", json={"voto": 3})
    assert mancante.status_code == 404
    assert mancante.json() == {"detail": "Chiamata non trovata."}

    chiamata = chiamata_ai(db)
    db.commit()
    utente_di_prova("artigiano")
    assert (
        client.post(f"/api/storico-ai/{chiamata.id}/voto", json={"voto": 3}).status_code
        == 403
    )
    utente_di_prova("admin")
    assert (
        client.post(f"/api/storico-ai/{chiamata.id}/voto", json={"voto": 3}).status_code
        == 200
    )
