"""Rigenera il testo di un post, da zero o da un testo proposto (plan §4, R-03, R-04, R-31).

CA-26, CA-27, CA-28, CA-66 (funzioni e job).
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.adapters.ai import AIFinto, usa_ai
from app.core.coda import RIGENERA_POST, accoda
from app.core.coda import app as coda_app
from app.core.errori import DatiNonValidi, NonTrovato, StatoNonValido
from app.moduli.contenuti import generazione, interventi, jobs
from app.moduli.contenuti.models import VersionePost
from app.moduli.contenuti.service import (
    accendi_intervento,
    ha_blocchi,
    puo_rigenerare,
)
from tests.moduli.accesso.fabbrica import utente
from tests.moduli.campagne.fabbrica import campagna_in_revisione
from tests.moduli.contenuti.fabbrica import post_approvato, post_da_approvare

ADESSO = datetime(2030, 1, 5, 12, tzinfo=timezone.utc)


@pytest.fixture
def ai() -> Iterator[AIFinto]:
    with usa_ai(AIFinto()) as finto:
        yield finto


@pytest.fixture(autouse=True)
def transazioni_di_prova(db, monkeypatch) -> None:
    """Il job apre le sue transazioni sulla sessione del test, a un'ora fissa."""

    @contextmanager
    def transazione():
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise

    monkeypatch.setattr(jobs, "transazione", transazione)
    monkeypatch.setattr(jobs, "adesso", lambda: ADESSO)


def _versioni(db, post) -> int:
    return db.scalar(
        select(func.count())
        .select_from(VersionePost)
        .where(VersionePost.post_id == post.id)
    )


def _post_con_intervento(db, tipo="rigenera_totale", **campi):
    uno = post_da_approvare(db, **campi)
    accendi_intervento(db, uno.id, tipo, ADESSO)
    db.commit()  # come dopo la richiesta: i dati restano se il job viene annullato
    return uno


# --- puo_rigenerare ---------------------------------------------------------------


def test_puo_rigenerare_in_revisione_su_un_post_da_approvare(db):
    uno = post_da_approvare(db)
    assert puo_rigenerare(db, uno.id, ADESSO) is True


def test_ca28_dopo_3_rigenerazioni_non_si_puo(db):
    assert puo_rigenerare(db, post_da_approvare(db, n_rigenerazioni_testo=2).id, ADESSO)
    quarta = post_da_approvare(db, n_rigenerazioni_testo=3)
    assert puo_rigenerare(db, quarta.id, ADESSO) is False


def test_ca29_in_campagna_attiva_non_si_puo(db):
    assert puo_rigenerare(db, post_approvato(db).id, ADESSO) is False


@pytest.mark.parametrize(
    "stato", ["approvato", "pubblicato", "fallito", "scaduto", "scartato", "annullato"]
)
def test_un_post_non_da_approvare_non_si_rigenera(db, stato):
    campagna = campagna_in_revisione(db)
    uno = post_da_approvare(db, campagna_id=campagna.id, stato=stato)
    assert puo_rigenerare(db, uno.id, ADESSO) is False


def test_con_un_intervento_in_corso_non_si_puo_ma_dopo_10_minuti_si(db):
    uno = post_da_approvare(
        db,
        intervento_in_corso="rigenera_totale",
        intervento_dal=ADESSO - timedelta(minutes=9),
    )
    assert puo_rigenerare(db, uno.id, ADESSO) is False
    uno.intervento_dal = ADESSO - timedelta(minutes=11)
    assert puo_rigenerare(db, uno.id, ADESSO) is True


def test_puo_rigenerare_post_inesistente(db):
    with pytest.raises(NonTrovato):
        puo_rigenerare(db, -1, ADESSO)


# --- accendi_intervento -----------------------------------------------------------


@pytest.mark.parametrize("tipo", ["rigenera_totale", "rigenera_da_proposta"])
def test_accendi_intervento_salva_tipo_e_ora(db, tipo):
    uno = post_da_approvare(db)
    assert accendi_intervento(db, uno.id, tipo, ADESSO) is uno
    assert (uno.intervento_in_corso, uno.intervento_dal) == (tipo, ADESSO)


def test_accendi_intervento_con_un_altro_intervento_in_corso_409(db):
    uno = _post_con_intervento(db)
    with pytest.raises(StatoNonValido):
        accendi_intervento(db, uno.id, "rigenera_da_proposta", ADESSO)
    assert uno.intervento_in_corso == "rigenera_totale"


def test_ca28_quarta_rigenerazione_409(db):
    uno = post_da_approvare(db, n_rigenerazioni_testo=3)
    with pytest.raises(StatoNonValido):
        accendi_intervento(db, uno.id, "rigenera_totale", ADESSO)
    assert uno.intervento_in_corso is None


def test_ca29_in_campagna_attiva_409(db):
    uno = post_approvato(db)
    with pytest.raises(StatoNonValido):
        accendi_intervento(db, uno.id, "rigenera_totale", ADESSO)


def test_accendi_intervento_tipo_sconosciuto_422(db):
    with pytest.raises(DatiNonValidi):
        accendi_intervento(db, post_da_approvare(db).id, "cambia_tutto", ADESSO)


def test_accendi_intervento_post_inesistente(db):
    with pytest.raises(NonTrovato):
        accendi_intervento(db, -1, "rigenera_totale", ADESSO)


# --- rigenera: da zero (CA-26) ----------------------------------------------------


def test_ca26_da_zero_nuova_versione_con_le_stesse_foto_validata(db, ai):
    operatore = utente(db, "operatore")
    uno = _post_con_intervento(db, controllato_da=operatore.id, controllato_il=ADESSO)
    prima = uno.versione_corrente
    foto_prima = [(l.posizione, l.foto_id) for l in prima.legami_foto]

    nuova = interventi.rigenera(db, uno.id, None, None, ADESSO)

    assert uno.versione_corrente is nuova
    assert (nuova.numero, nuova.tipo_intervento, nuova.autore_id) == (
        2,
        "rigenera_totale",
        None,
    )
    assert [(l.posizione, l.foto_id) for l in nuova.legami_foto] == foto_prima
    assert nuova.errori_validazione == []
    assert (nuova.provider_ai, nuova.modello_ai) == ("finto", "finto")
    assert nuova.testo != prima.testo
    assert (nuova.testo_proposto, nuova.nota) == (None, None)
    # Il ciclo si conta, l'intervento si spegne, la spunta cade, la precedente resta.
    assert uno.n_rigenerazioni_testo == 1
    assert (uno.intervento_in_corso, uno.intervento_dal) == (None, None)
    assert (uno.controllato_da, uno.controllato_il) == (None, None)
    assert uno.da_rivedere is False
    assert prima.testo == "Testo di prova"


def test_il_testo_dell_ai_si_salva_senza_caratteri_nulli(db, ai):
    """T3-906: un NUL nella risposta dell'AI non fa fallire la rigenerazione."""
    uno = _post_con_intervento(db)
    ai.comanda_testo("Un testo con un carattere nullo\x00 dentro.", volte=1)

    nuova = interventi.rigenera(db, uno.id, None, None, ADESSO)

    assert nuova.testo == "Un testo con un carattere nullo dentro."


def test_r04_le_versioni_rifiutate_arrivano_all_ai_e_non_si_ripetono(db, ai):
    uno = _post_con_intervento(db)
    prima = uno.versione_corrente.testo
    seconda = interventi.rigenera(db, uno.id, None, None, ADESSO)
    accendi_intervento(db, uno.id, "rigenera_totale", ADESSO)
    terza = interventi.rigenera(db, uno.id, None, None, ADESSO)

    chiamate = [c for c in ai.chiamate if c["operazione"] == "genera_post"]
    assert chiamate[0]["rifiutate"] == [prima]
    assert chiamate[1]["rifiutate"] == [prima, seconda.testo]
    assert len({prima, seconda.testo, terza.testo}) == 3
    assert uno.n_rigenerazioni_testo == 2


def test_la_rigenerazione_con_un_blocco_che_resta_lascia_il_post_da_rivedere(db, ai):
    uno = _post_con_intervento(db)
    ai.comanda_testo("Fatto a mano, gratis!", ["a"], volte=None)

    nuova = interventi.rigenera(db, uno.id, None, None, ADESSO)

    assert [e["livello"] for e in nuova.errori_validazione] == ["blocco"]
    assert uno.da_rivedere is True
    assert uno.n_rigenerazioni_testo == 1
    # R-09: il testo si è riscritto 3 volte prima di arrendersi.
    assert len([c for c in ai.chiamate if c["operazione"] == "genera_post"]) == 1 + 3


def test_la_rigenerazione_riscrive_se_il_validatore_trova_un_blocco(db, ai):
    uno = _post_con_intervento(db)
    ai.comanda_testo("Fatto a mano, gratis!", ["a"], volte=1)
    nuova = interventi.rigenera(db, uno.id, None, None, ADESSO)
    assert nuova.errori_validazione == []
    assert "gratis" not in nuova.testo
    assert uno.da_rivedere is False


def test_la_rigenerazione_toglie_da_rivedere_se_il_testo_nuovo_e_a_posto(db, ai):
    uno = _post_con_intervento(db, da_rivedere=True)
    interventi.rigenera(db, uno.id, None, None, ADESSO)
    assert uno.da_rivedere is False


# --- rigenera: da proposta (CA-27) ------------------------------------------------


def test_ca27_da_proposta_con_testo_e_nota(db, ai):
    uno = _post_con_intervento(db, "rigenera_da_proposta")
    nuova = interventi.rigenera(
        db, uno.id, "  Il mio testo.  ", "Più caldo, per favore", ADESSO
    )
    assert (nuova.tipo_intervento, nuova.testo) == (
        "rigenera_da_proposta",
        "Il mio testo.",
    )
    assert (nuova.testo_proposto, nuova.nota) == (
        "Il mio testo.",
        "Più caldo, per favore",
    )
    chiamata = [c for c in ai.chiamate if c["operazione"] == "genera_post"][-1]
    assert (chiamata["testo_proposto"], chiamata["nota"]) == (
        "Il mio testo.",
        "Più caldo, per favore",
    )
    assert [(l.posizione, l.foto_id) for l in nuova.legami_foto] == [
        (l.posizione, l.foto_id) for l in uno.versioni[0].legami_foto
    ]
    assert uno.n_rigenerazioni_testo == 1


def test_ca27_da_proposta_senza_testo_422_e_nessuna_versione(db, ai):
    uno = _post_con_intervento(db, "rigenera_da_proposta")
    for vuoto in (None, "", "   "):
        with pytest.raises(DatiNonValidi):
            interventi.rigenera(db, uno.id, vuoto, None, ADESSO)
    assert _versioni(db, uno) == 1


def test_da_zero_ignora_un_testo_proposto(db, ai):
    uno = _post_con_intervento(db)
    nuova = interventi.rigenera(db, uno.id, "Ignorato", None, ADESSO)
    assert nuova.testo_proposto is None and nuova.testo != "Ignorato"


# --- rigenera: quando non fa nulla ------------------------------------------------


def test_non_fa_nulla_senza_un_intervento_di_rigenerazione(db, ai):
    uno = post_da_approvare(db)
    assert interventi.rigenera(db, uno.id, None, None, ADESSO) is None
    uno.intervento_in_corso = "ritocco_foto"
    assert interventi.rigenera(db, uno.id, None, None, ADESSO) is None
    assert _versioni(db, uno) == 1 and ai.chiamate == []


def test_non_fa_nulla_se_la_campagna_non_e_in_revisione(db, ai):
    uno = _post_con_intervento(db)
    campagna = interventi.campagne.campagna(db, uno.campagna_id)
    campagna.stato = "attiva"
    assert interventi.rigenera(db, uno.id, None, None, ADESSO) is None
    assert _versioni(db, uno) == 1 and ai.chiamate == []


@pytest.mark.parametrize("stato", ["approvato", "scaduto", "scartato"])
def test_non_fa_nulla_se_il_post_non_e_da_approvare(db, ai, stato):
    uno = _post_con_intervento(db)
    uno.stato = stato
    assert interventi.rigenera(db, uno.id, None, None, ADESSO) is None
    assert _versioni(db, uno) == 1 and ai.chiamate == []


def test_non_fa_nulla_per_un_post_inesistente(db, ai):
    assert interventi.rigenera(db, -1, None, None, ADESSO) is None


# --- il job (CA-66) ---------------------------------------------------------------


def test_job_riuscito_non_chiede_un_altra_esecuzione(db, ai):
    uno = _post_con_intervento(db)
    assert jobs.esegui_rigenerazione(uno.id, None, None, 1) is False
    assert uno.versione_corrente.numero == 2
    assert uno.intervento_in_corso is None


def test_ca66_dopo_3_esecuzioni_fallite_il_post_resta_com_e(db, ai):
    uno = _post_con_intervento(db)
    ai.comanda_errore("genera_post", "temporaneo", volte=None)

    assert jobs.esegui_rigenerazione(uno.id, None, None, 1) is True
    assert uno.intervento_in_corso == "rigenera_totale"
    assert jobs.esegui_rigenerazione(uno.id, None, None, 2) is True
    assert uno.intervento_in_corso == "rigenera_totale"
    assert jobs.esegui_rigenerazione(uno.id, None, None, 3) is False

    assert _versioni(db, uno) == 1
    assert uno.versione_corrente.testo == "Testo di prova"
    assert uno.n_rigenerazioni_testo == 0
    assert (uno.intervento_in_corso, uno.intervento_dal) == (None, None)


def test_job_riesce_alla_seconda_esecuzione_e_conta_un_solo_ciclo(db, ai):
    uno = _post_con_intervento(db)
    ai.comanda_errore("genera_post", "risposta", volte=1)
    assert jobs.esegui_rigenerazione(uno.id, None, None, 1) is True
    assert jobs.esegui_rigenerazione(uno.id, None, None, 2) is False
    assert (uno.versione_corrente.numero, uno.n_rigenerazioni_testo) == (2, 1)


def test_un_errore_di_configurazione_spegne_subito_l_intervento(db, ai):
    uno = _post_con_intervento(db)
    ai.comanda_errore("genera_post", "configurazione", volte=None)
    assert jobs.esegui_rigenerazione(uno.id, None, None, 1) is False
    assert uno.intervento_in_corso is None
    assert uno.n_rigenerazioni_testo == 0 and _versioni(db, uno) == 1


def test_da_proposta_senza_testo_spegne_subito_l_intervento(db, ai):
    uno = _post_con_intervento(db, "rigenera_da_proposta")
    assert jobs.esegui_rigenerazione(uno.id, None, None, 1) is False
    assert uno.intervento_in_corso is None and _versioni(db, uno) == 1


def test_ca66_un_intervento_partito_da_piu_di_10_minuti_non_blocca_l_approvazione(
    db, ai
):
    uno = _post_con_intervento(db)
    assert ha_blocchi(db, uno.campagna_id, ADESSO + timedelta(minutes=5)) is True
    assert ha_blocchi(db, uno.campagna_id, ADESSO + timedelta(minutes=11)) is False


def test_il_job_e_registrato_con_tre_esecuzioni_a_trenta_secondi():
    task = coda_app.tasks[RIGENERA_POST]

    assert task.pass_context is True
    assert generazione.ESECUZIONI == 3
    assert task.retry_strategy.max_attempts == 2
    assert task.retry_strategy.wait == 30
    assert task.retry_strategy.retry_exceptions == [jobs.NuovaEsecuzione]


def test_il_job_accodato_per_nome_arriva_in_fondo(db, ai, coda, monkeypatch):
    """Come da /rigenera: accendi l'intervento, accoda per nome, esegue il worker."""
    monkeypatch.setattr(coda_app.periodic_registry, "periodic_tasks", {})
    uno = _post_con_intervento(db, "rigenera_da_proposta")
    db.commit()
    job_id = accoda(
        RIGENERA_POST, post_id=uno.id, testo_proposto="Testo mio.", nota="Grazie"
    )

    coda_app.run_worker(wait=False, install_signal_handlers=False, listen_notify=False)

    assert coda.jobs[job_id]["status"] == "succeeded"
    db.expire_all()
    assert uno.versione_corrente.testo == "Testo mio."
    assert uno.versione_corrente.nota == "Grazie"
    assert uno.intervento_in_corso is None


def test_il_job_che_fallisce_torna_in_coda(db, ai, coda, monkeypatch):
    monkeypatch.setattr(coda_app.periodic_registry, "periodic_tasks", {})
    uno = _post_con_intervento(db)
    db.commit()
    ai.comanda_errore("genera_post", "temporaneo", volte=None)
    job_id = accoda(RIGENERA_POST, post_id=uno.id)
    prima = datetime.now(timezone.utc)

    coda_app.run_worker(wait=False, install_signal_handlers=False, listen_notify=False)

    job = coda.jobs[job_id]
    assert (job["status"], job["attempts"]) == ("todo", 1)
    assert job["scheduled_at"] - prima >= timedelta(seconds=29)
    db.expire_all()
    assert uno.intervento_in_corso == "rigenera_totale"


def test_ca107_la_rigenerazione_passa_gli_attacchi_degli_altri_post(db, ai):
    uno = _post_con_intervento(db)
    post_da_approvare(db, campagna_id=uno.campagna_id)  # stesso canale
    db.commit()

    interventi.rigenera(db, uno.id, None, None, ADESSO)

    chiamata = [c for c in ai.chiamate if c["operazione"] == "genera_post"][-1]
    assert chiamata["altri_post"] == ["Testo di prova"]
