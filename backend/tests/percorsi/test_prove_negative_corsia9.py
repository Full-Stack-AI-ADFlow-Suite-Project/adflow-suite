"""T3-927, passo 9 di converge §4: le due prove negative che il percorso a mano
non poteva fare con l'AI finta, dalle API vere.

1. «Modifica di un post che esce entro 15 minuti»: dopo l'approvazione modifica,
   sposta, annulla e cambia foto sono rifiutati (409) e il post resta com'era;
   un post che esce più tardi si modifica.
2. «Approva con un post da rivedere»: l'approvazione è rifiutata (409), la
   campagna resta in revisione e nessun post cambia stato.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.moduli.contenuti.models import Post
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_approvato, post_da_approvare


def test_post_che_esce_entro_15_minuti_non_si_tocca(db, client, utente_di_prova):
    campagna = campagna_attiva(db)
    adesso = datetime.now(timezone.utc)
    vicino = post_approvato(
        db, campagna_id=campagna.id, data_ora=adesso + timedelta(minutes=10)
    )
    lontano = post_approvato(
        db, campagna_id=campagna.id, data_ora=adesso + timedelta(hours=3)
    )
    utente_di_prova("operatore")
    nuova = (adesso + timedelta(days=2)).isoformat()

    for risposta in (
        client.post(f"/api/post/{vicino.id}/modifica", json={"testo": "Nuovo"}),
        client.post(f"/api/post/{vicino.id}/sposta", json={"data_ora": nuova}),
        client.post(f"/api/post/{vicino.id}/annulla", json={"nota": "motivo"}),
        client.post(f"/api/post/{vicino.id}/cambia-foto", json={"foto_id": 1}),
    ):
        assert risposta.status_code == 409, risposta.text
        assert isinstance(risposta.json()["detail"], str)

    db.refresh(vicino)
    assert vicino.stato == "approvato"
    assert len(vicino.versioni) == 1

    assert (
        client.post(
            f"/api/post/{lontano.id}/modifica", json={"testo": "Nuovo"}
        ).status_code
        == 200
    )
    db.refresh(lontano)
    assert len(lontano.versioni) == 2


def test_approva_con_un_post_da_rivedere_409(db, client, utente_di_prova):
    campagna = campagna_in_revisione(db)
    post_da_approvare(db, campagna_id=campagna.id, da_rivedere=True)
    post_da_approvare(db, campagna_id=campagna.id, canale="facebook")
    utente_di_prova("operatore")

    risposta = client.post(f"/api/campagne/{campagna.id}/approva")

    assert risposta.status_code == 409, risposta.text
    db.refresh(campagna)
    assert campagna.stato == "in_revisione"
    stati = db.scalars(select(Post.stato).where(Post.campagna_id == campagna.id)).all()
    assert set(stati) == {"da_approvare"}
