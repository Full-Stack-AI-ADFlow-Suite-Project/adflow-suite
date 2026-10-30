"""T3-908: rigenera l'immagine AI di un post (spec R-49, CA-102, CA-103)."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.adapters.ai import AIFinto, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.errori import StatoNonValido
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import interventi
from app.moduli.contenuti.domain import DICITURA_IMMAGINE_AI, IMMAGINE_AI
from app.moduli.contenuti.immagini_ai import blocco_immagine_non_creata
from app.moduli.contenuti.models import (
    ChiamataAI,
    Post,
    VersionePost,
    VersionePostFoto,
)
from app.moduli.contenuti.service import (
    accendi_rigenerazione_immagine,
    costo_ai_della_campagna,
)
from tests.moduli.campagne.fabbrica import campagna_attiva, campagna_in_revisione
from tests.moduli.contenuti.fabbrica import uscita as fabbrica_uscita

# I post della fabbrica escono il 5/1/2030 alle 12:00 UTC.
ADESSO = datetime(2030, 1, 5, 9, tzinfo=timezone.utc)
PROMPT_VECCHIO = "un banco di lavoro al tramonto"


@pytest.fixture
def ai():
    """Il provider finto con un costo per chiamata, e l'archivio in memoria."""
    with usa_ai(AIFinto(costo_chiamata=Decimal("0.04"))) as finto:
        with usa_archivio(ArchivioFinto()):
            yield finto


def _foto_ai(db, campagna, prompt: str = PROMPT_VECCHIO):
    una = campagne.aggiungi_foto(
        db, campagna.id, "creata_ai", "immagine-ai.png", "image/png", 64, 64
    )
    campagne.aggiorna_foto(
        db,
        una.id,
        {"prompt": prompt, "versione_prompt": "immagine_v2", "nota": None},
        0,
    )
    return una


def _post(
    db,
    campagna,
    uscita,
    foto,
    canale: str = "instagram",
    testo: str = f"Testo di prova\n\n{DICITURA_IMMAGINE_AI}",
    riempitivo: str | None = IMMAGINE_AI,
    errori: list[dict] | None = None,
):
    record = Post(
        campagna_id=campagna.id,
        uscita_id=uscita.id,
        canale=canale,
        riempitivo=riempitivo,
        data_ora=datetime(2030, 1, 5, 12, tzinfo=timezone.utc),
        stato="da_approvare",
    )
    db.add(record)
    db.flush()
    versione = VersionePost(
        post_id=record.id,
        numero=1,
        testo=testo,
        hashtag=["artigianato"],
        tipo_intervento="generazione",
        provider_ai="finto",
        modello_ai="finto",
        versione_prompt="test-1",
        errori_validazione=errori,
    )
    db.add(versione)
    db.flush()
    if foto is not None:
        db.add(VersionePostFoto(versione_id=versione.id, posizione=1, foto_id=foto.id))
    db.flush()
    db.expire(record, ["versioni"])
    return record


def _scena(db):
    """Campagna in revisione, un'uscita e due post che usano la sua immagine AI."""
    campagna = campagna_in_revisione(db)
    mazzo = campagne.gruppi_della_campagna(db, campagna.id)[0]
    uscita = fabbrica_uscita(db, campagna, mazzo)
    vecchia = _foto_ai(db, campagna)
    primo = _post(db, campagna, uscita, vecchia, "instagram")
    gemello = _post(db, campagna, uscita, vecchia, "facebook")
    return campagna, uscita, vecchia, primo, gemello


def _chiamate_immagine(db, campagna) -> int:
    return db.scalar(
        select(func.count())
        .select_from(ChiamataAI)
        .where(
            ChiamataAI.campagna_id == campagna.id,
            ChiamataAI.tipo == "immagine",
        )
    )


def test_ca102_rigenera_immagine_su_tutti_i_post_dell_uscita(db, ai):
    """CA-102: nuova foto con prompt e nota, una versione su ogni post dell'uscita."""
    campagna, uscita, vecchia, primo, gemello = _scena(db)

    accendi_rigenerazione_immagine(db, primo.id, False, None, ADESSO)
    assert primo.intervento_in_corso == "rigenera_immagine"
    assert gemello.intervento_in_corso == "rigenera_immagine"

    versioni = interventi.rigenera_immagine(
        db, primo.id, "più luce del mattino", False, None, ADESSO
    )
    assert versioni is not None and len(versioni) == 2

    nuova = versioni[0].legami_foto[0].foto_id
    assert nuova != vecchia.id
    foto_nuova = campagne.foto_per_id(db, [nuova])[0]
    assert foto_nuova.origine == "creata_ai"
    assert foto_nuova.analisi_ai["nota"] == "più luce del mattino"
    assert "più luce del mattino" in foto_nuova.analisi_ai["prompt"]
    # Il prompt delle immagini già avute arriva all'AI come «da non ripetere».
    prompt = ai.chiamate[-1]["prompt"]
    assert PROMPT_VECCHIO in prompt

    # La foto vecchia resta (costituzione §1.2).
    assert campagne.foto_per_id(db, [vecchia.id]) != []

    for post in (primo, gemello):
        db.refresh(post)
        assert post.versione_corrente.tipo_intervento == "rigenera_immagine"
        assert post.versione_corrente.legami_foto[0].foto_id == nuova
        assert post.intervento_in_corso is None
    # Stesso testo di prima: la dicitura non si duplica.
    assert primo.versione_corrente.testo.count(DICITURA_IMMAGINE_AI) == 1
    # Il costo della chiamata è registrato (R-44).
    assert _chiamate_immagine(db, campagna) == 1
    assert costo_ai_della_campagna(db, campagna.id) == Decimal("0.04")


def test_ca102_il_blocco_immagine_non_creata_sparisce(db, ai):
    """CA-102: un post senza immagine esce dalla rigenerazione senza il blocco."""
    campagna = campagna_in_revisione(db)
    mazzo = campagne.gruppi_della_campagna(db, campagna.id)[0]
    uscita = fabbrica_uscita(db, campagna, mazzo)
    post = _post(
        db,
        campagna,
        uscita,
        None,
        riempitivo=IMMAGINE_AI,
        errori=[blocco_immagine_non_creata("Il servizio AI ha rifiutato.")],
    )

    accendi_rigenerazione_immagine(db, post.id, False, None, ADESSO)
    interventi.rigenera_immagine(db, post.id, None, False, None, ADESSO)

    db.refresh(post)
    assert post.da_rivedere is False
    assert post.versione_corrente.errori_validazione == []
    assert post.versione_corrente.legami_foto[0].foto_id != 0


def test_ca102_quarta_rigenerazione_dell_immagine_409(db, ai):
    """CA-102: dopo 3 versioni `rigenera_immagine` la quarta è 409."""
    _, uscita, vecchia, primo, gemello = _scena(db)
    for numero in range(2, 5):
        db.add(
            VersionePost(
                post_id=primo.id,
                numero=numero,
                testo="Testo di prova",
                hashtag=["artigianato"],
                tipo_intervento="rigenera_immagine",
            )
        )
    db.flush()
    db.expire(primo, ["versioni"])

    with pytest.raises(StatoNonValido, match="già stata rigenerata 3 volte"):
        accendi_rigenerazione_immagine(db, primo.id, False, None, ADESSO)
    assert primo.intervento_in_corso is None
    assert gemello.intervento_in_corso is None


def test_ca102_campagna_attiva_409(db, ai):
    """CA-102: dopo l'approvazione nessuna immagine AI (R-16)."""
    campagna = campagna_attiva(db)
    mazzo = campagne.gruppi_della_campagna(db, campagna.id)[0]
    uscita = fabbrica_uscita(db, campagna, mazzo)
    post = _post(db, campagna, uscita, None)

    with pytest.raises(StatoNonValido):
        accendi_rigenerazione_immagine(db, post.id, False, None, ADESSO)


def test_ca102_intervento_in_corso_409(db):
    """CA-102, R-31: con un intervento in corso non se ne accende un altro."""
    _, _, _, primo, _ = _scena(db)
    primo.intervento_in_corso = "rigenera_totale"
    primo.intervento_dal = ADESSO
    db.flush()

    with pytest.raises(StatoNonValido, match="intervento in corso"):
        accendi_rigenerazione_immagine(db, primo.id, False, None, ADESSO)


def test_ca103_foto_vera_solo_quel_post_diventa_immagine_ai(db, ai):
    """CA-103: su una foto vera la rigenerazione tocca solo quel post."""
    campagna = campagna_in_revisione(db)
    mazzo = campagne.gruppi_della_campagna(db, campagna.id)[0]
    uscita = fabbrica_uscita(db, campagna, mazzo)
    vera = mazzo.foto[0]
    post = _post(
        db,
        campagna,
        uscita,
        vera,
        riempitivo=None,
        testo="Testo di prova",
    )

    accendi_rigenerazione_immagine(db, post.id, False, None, ADESSO)
    versioni = interventi.rigenera_immagine(db, post.id, None, False, None, ADESSO)

    assert versioni is not None and len(versioni) == 1
    db.refresh(post)
    assert post.riempitivo == IMMAGINE_AI
    assert post.versione_corrente.testo.endswith(DICITURA_IMMAGINE_AI)
    assert post.versione_corrente.legami_foto[0].foto_id != vera.id


def test_ca103_riscrivi_testo_segue_una_rigenerazione_e_un_ciclo(db, ai):
    """CA-103: «Riscrivi anche il testo» crea `rigenera_totale` e conta un ciclo."""
    _, _, _, primo, _ = _scena(db)

    accendi_rigenerazione_immagine(db, primo.id, True, "tono più caldo", ADESSO)
    versioni = interventi.rigenera_immagine(
        db, primo.id, "più luce", True, "tono più caldo", ADESSO
    )

    assert versioni is not None
    # Due versioni `rigenera_immagine` e una `rigenera_totale` per ogni post toccato.
    tipi = [una.tipo_intervento for una in versioni]
    assert tipi == [
        "rigenera_immagine",
        "rigenera_immagine",
        "rigenera_totale",
        "rigenera_totale",
    ]
    assert versioni[-1].nota == "tono più caldo"
    db.refresh(primo)
    assert primo.n_rigenerazioni_testo == 1
    assert primo.intervento_in_corso is None


def test_ca103_riscrivi_testo_senza_cicli_409_e_nessuna_versione(db, ai):
    """CA-103: senza rigenerazioni del testo rimaste è 409, e il post non cambia."""
    _, _, _, primo, _ = _scena(db)
    primo.n_rigenerazioni_testo = 3
    db.flush()
    versioni_prima = len(primo.versioni)

    with pytest.raises(StatoNonValido, match="non si può più rigenerare"):
        accendi_rigenerazione_immagine(db, primo.id, True, None, ADESSO)

    assert len(primo.versioni) == versioni_prima
    assert primo.intervento_in_corso is None
    assert _chiamate_immagine(db, campagne.campagna(db, primo.campagna_id)) == 0


def test_ca102_due_rifiuti_del_provider_nessuna_versione(db, ai):
    """CA-102, R-49: due rifiuti lasciano i post com'erano e spengono l'intervento."""
    _, _, _, primo, gemello = _scena(db)
    ai.comanda_errore("genera_immagine", "rifiuto", volte=None)
    accendi_rigenerazione_immagine(db, primo.id, False, None, ADESSO)
    versioni_prima = len(primo.versioni)

    assert interventi.rigenera_immagine(db, primo.id, None, False, None, ADESSO) is None

    db.expire_all()
    assert len(primo.versioni) == versioni_prima
    assert primo.intervento_in_corso is None
    assert gemello.intervento_in_corso is None


def test_ca102_la_rotta_accende_l_intervento_e_accoda_il_job(
    client, utente_di_prova, db, coda, ai
):
    """CA-102: `POST /post/{id}/rigenera-immagine` risponde «in corso» e accoda il job."""
    from app.core.coda import RIGENERA_IMMAGINE

    _, _, _, primo, gemello = _scena(db)
    utente_di_prova("operatore")

    risposta = client.post(
        f"/api/post/{primo.id}/rigenera-immagine",
        json={"nota": "più luce", "riscrivi_testo": True, "nota_testo": "tono caldo"},
    )

    assert risposta.status_code == 200
    assert risposta.json() == {"stato": "in_corso"}
    assert primo.intervento_in_corso == "rigenera_immagine"
    assert gemello.intervento_in_corso == "rigenera_immagine"
    [job] = coda.jobs.values()
    assert job["task_name"] == RIGENERA_IMMAGINE
    assert job["args"] == {
        "post_id": primo.id,
        "nota": "più luce",
        "riscrivi_testo": True,
        "nota_testo": "tono caldo",
    }


def test_ca102_la_rotta_risponde_409_fuori_dalla_revisione(
    client, utente_di_prova, db, coda, ai
):
    """CA-102: la rotta risponde 409 e non accoda niente."""
    campagna = campagna_attiva(db)
    mazzo = campagne.gruppi_della_campagna(db, campagna.id)[0]
    uscita = fabbrica_uscita(db, campagna, mazzo)
    post = _post(db, campagna, uscita, None)
    utente_di_prova("operatore")

    risposta = client.post(f"/api/post/{post.id}/rigenera-immagine", json={})

    assert risposta.status_code == 409
    assert coda.jobs == {}
