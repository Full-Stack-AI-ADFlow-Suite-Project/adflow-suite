"""T1-34: job `genera_campagna` a tappe (plan §4, spec §2.2, R-24, R-35).

CA-17, CA-18, CA-19 (fino a `generazione_fallita`), CA-20, CA-50,
CA-57 (il post `immagine_ai` ha la sua immagine e il suo testo: T3-34, per il resto
`test_immagini_ai.py`), CA-58, CA-59,
CA-80 (le foto migliori per punteggio); poi la ripresa dalle tappe già salvate
e gli errori tecnici secondo il tipo.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

import app.adapters.ai as modulo_ai
from app.adapters.ai import AIFinto, imposta_ai, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.core.config import leggi_impostazioni
from app.core.coda import GENERA_CAMPAGNA, accoda
from app.core.coda import app as coda_app
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import generazione, jobs
from app.moduli.contenuti.models import ErroreGenerazione, Post
from app.moduli.contenuti.service import (
    piano_corrente,
    post_della_campagna,
    ultimo_errore,
    uscite_della_campagna,
)
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import (
    campagna_conclusa,
    campagna_in_bozza,
    campagna_inviata,
    foto,
    gruppo_di_archivio,
)

INIZIO = date(2030, 1, 7)
FINE = date(2030, 1, 20)  # 14 giorni: con 3 post a settimana, 6 post chiesti
ADESSO = datetime(2030, 1, 1, 9, tzinfo=timezone.utc)
DUE_CANALI = ["facebook", "instagram"]
IDONEA = {"idonea": True, "simile_a": None}


@pytest.fixture(autouse=True)
def archivio() -> Iterator[ArchivioFinto]:
    """Le immagini AI nascono in un archivio in memoria, non su disco."""
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


@pytest.fixture
def ai() -> Iterator[AIFinto]:
    with usa_ai(AIFinto()) as finto:
        yield finto


@pytest.fixture(autouse=True)
def transazioni_di_prova(db, monkeypatch) -> None:
    """Il job apre le sue transazioni sulla sessione del test, a un'ora fissa.

    Come nel worker: commit alla fine di ogni passo, rollback se c'è un errore.
    """

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


def _campagna(db, *, n_foto: int = 6, canali=DUE_CANALI, **campi):
    """Campagna `inviata` di 14 giorni con un gruppo di ``n_foto`` foto (almeno 4)."""
    bottega = profilo(
        db,
        nome="Ceramiche Bianchi",
        canali=list(canali),
        frequenza="f3_4",
        vincoli="Non parlare di sconti.",
    )
    stato = campi.pop("stato", None)
    dati = dict(profilo_id=bottega.id, inizio=INIZIO, fine=FINE)
    dati.update(campi)
    campagna = campagna_inviata(db, **dati)
    if stato is not None:
        campagna.stato = stato  # la fabbrica la crea `inviata`
    mazzo = campagne.gruppi_della_campagna(db, campagna.id)[0]
    for _ in range(n_foto - 4):
        foto(db, gruppo=mazzo)
    db.commit()  # come dopo l'invio: i dati restano se un passo viene annullato
    return campagna


def _foto_ids(db, campagna) -> list[int]:
    return [f.id for f in campagne.foto_della_campagna(db, campagna.id)]


def _job(campagna_id: int) -> int:
    """Il job come lo esegue Procrastinate: al massimo 3 esecuzioni. Dice quante."""
    for esecuzione in range(1, generazione.ESECUZIONI + 1):
        if not jobs.esegui_generazione(campagna_id, esecuzione):
            return esecuzione
    raise AssertionError("Alla terza esecuzione il job non chiede di ripartire.")


def _errori(db, campagna) -> list[ErroreGenerazione]:
    return list(
        db.scalars(
            select(ErroreGenerazione)
            .where(ErroreGenerazione.campagna_id == campagna.id)
            .order_by(ErroreGenerazione.id)
        )
    )


def _post_del_canale(db, campagna, canale: str) -> list[Post]:
    return [p for p in post_della_campagna(db, campagna.id) if p.canale == canale]


def _foto_del_post(post: Post) -> list[int]:
    return [legame.foto_id for legame in post.versione_corrente.legami_foto]


def _chiamate(ai: AIFinto, operazione: str) -> list[dict]:
    return [c for c in ai.chiamate if c["operazione"] == operazione]


def _riprova(db, campagna) -> None:
    """Ciò che fa Riprova in `campagne` (T1-24): da fallita torna `inviata`."""
    campagne.cambia_stato(db, campagna, "inviata")
    db.commit()


# --- Il percorso che riesce ---------------------------------------------------


def test_ca20_generazione_riuscita_piano_salvato_e_campagna_in_revisione(db, ai):
    campagna = _campagna(db)

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    piano = piano_corrente(db, campagna.id)
    assert (piano.numero, piano.debole, piano.esito_controllo) == (1, False, [])
    assert (piano.provider_ai, piano.modello_ai) == ("finto", "finto")
    assert piano.versione_prompt == "finto-1"
    assert piano.strategia == piano.contenuto["strategia"]
    post = post_della_campagna(db, campagna.id)
    assert len(post) == 12
    for uno in post:
        assert uno.stato == "da_approvare"
        assert uno.da_rivedere is False
        assert len(uno.versioni) == 1
        versione = uno.versione_corrente
        assert (versione.numero, versione.tipo_intervento) == (1, "generazione")
        assert versione.autore_id is None
        assert (versione.provider_ai, versione.versione_prompt) == ("finto", "finto-1")
        assert versione.testo and versione.hashtag
        assert versione.errori_validazione == []
    assert _errori(db, campagna) == []


def test_ca17_sei_uscite_sei_post_per_canale_cinque_foto_e_un_immagine_ai(db, ai):
    """14 giorni, 3 post/sett., 2 canali, un gruppo di 5 foto idonee e diverse."""
    campagna = _campagna(db, n_foto=5)
    caricate = set(_foto_ids(db, campagna))

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    uscite = uscite_della_campagna(db, campagna.id)
    assert [u.numero for u in uscite] == [1, 2, 3, 4, 5, 6]
    for canale in DUE_CANALI:
        post = _post_del_canale(db, campagna, canale)
        assert len(post) == 6
        assert [p.riempitivo for p in post] == [None] * 5 + ["immagine_ai"]
        con_foto = [_foto_del_post(p) for p in post[:5]]
        assert all(len(foto_del_post) == 1 for foto_del_post in con_foto)
        usate = [foto_del_post[0] for foto_del_post in con_foto]
        # nessuna foto due volte sullo stesso canale, tutte tra quelle caricate
        assert len(set(usate)) == 5
        assert set(usate) == caricate
    assert uscite[5].gruppo_id is None
    assert uscite[0].gruppo_id is not None


def test_ca57_i_post_che_mancano_sono_immagini_ai_con_la_loro_immagine_e_il_loro_testo(
    db, ai
):
    """4 foto e 6 post chiesti: 2 `immagine_ai` per canale, ognuno con immagine e testo."""
    ai.carosello = True  # anche se chiesto: un post è una foto
    campagna = _campagna(db, n_foto=4)

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    assert piano_corrente(db, campagna.id).debole is False
    foto_della_campagna = campagne.foto_della_campagna(db, campagna.id)
    assert (
        sorted(f.origine for f in foto_della_campagna)
        == ["caricata"] * 4 + ["creata_ai"] * 2
    )
    per_canale = {c: _post_del_canale(db, campagna, c) for c in DUE_CANALI}
    for post in per_canale.values():
        assert len(post) == 6
        assert {p.formato for p in post} == {"singola"}
        assert [p.riempitivo for p in post] == [None] * 4 + ["immagine_ai"] * 2
        assert all(p.stato == "da_approvare" for p in post)
        for rimpiazzo in post[4:]:
            assert len(_foto_del_post(rimpiazzo)) == 1
            assert rimpiazzo.versione_corrente.testo.endswith("Immagine creata con AI")
            assert rimpiazzo.versione_corrente.errori_validazione == []
            assert rimpiazzo.da_rivedere is False
    # la stessa uscita su entrambi i canali ha la stessa immagine
    facebook, instagram = per_canale["facebook"], per_canale["instagram"]
    assert [p.uscita_id for p in facebook[4:]] == [p.uscita_id for p in instagram[4:]]
    assert [_foto_del_post(p) for p in facebook[4:]] == [
        _foto_del_post(p) for p in instagram[4:]
    ]
    assert len(_chiamate(ai, "genera_post")) == 12
    assert len(_chiamate(ai, "genera_immagine")) == 2


def test_ca57_senza_foto_la_campagna_e_tutta_di_immagini_ai(db, ai):
    """Il minimo di foto non c'è più (A5): la generazione parte e il piano è completo."""
    campagna = _campagna(db)
    for una in campagne.foto_della_campagna(db, campagna.id):
        ai.comanda_analisi(una.id, idonea=False, motivo="Foto scura")

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    post = post_della_campagna(db, campagna.id)
    assert len(post) == 12
    assert {p.riempitivo for p in post} == {"immagine_ai"}
    assert all(len(_foto_del_post(p)) == 1 and p.versione_corrente.testo for p in post)
    # un'immagine per uscita, non una per post
    assert len({tuple(_foto_del_post(p)) for p in post}) == 6


def test_ca80_all_ai_vanno_le_foto_migliori_per_punteggio_e_le_altre_restano_fuori(
    db, ai
):
    """10 foto idonee e diverse, 6 post chiesti: le 6 di punteggio più alto."""
    campagna = _campagna(db, n_foto=10)
    ids = _foto_ids(db, campagna)
    punteggi = [3, 5, 1, 4, 2, 5, 4, 1, 3, 2]
    for foto_id, punteggio in zip(ids, punteggi):
        ai.comanda_analisi(foto_id, punteggio=punteggio)
    migliori = [ids[n] for n in (1, 5, 3, 6, 0, 8)]  # a parità, l'id più basso

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    for canale in DUE_CANALI:
        post = _post_del_canale(db, campagna, canale)
        assert [p.riempitivo for p in post] == [None] * 6
        assert [_foto_del_post(p) for p in post] == [[n] for n in migliori]
    # le altre quattro restano non usate: non vanno nemmeno all'AI
    assert {
        f.id: f.n_utilizzi for f in campagne.foto_della_campagna(db, campagna.id)
    } == {n: (2 if n in migliori else 0) for n in ids}
    (piano,) = _chiamate(ai, "pianifica_campagna")
    assert piano["riscrittura"] is False


def test_ca80_il_piano_riceve_solo_le_foto_preselezionate(db, ai, monkeypatch):
    campagna = _campagna(db, n_foto=8)
    ids = _foto_ids(db, campagna)
    for foto_id, punteggio in zip(ids, [1, 1, 5, 5, 4, 4, 3, 3]):
        ai.comanda_analisi(foto_id, punteggio=punteggio)
    viste = []
    pianifica = ai.pianifica_campagna

    def pianifica_e_guarda(snapshot, campagna_ai, gruppi, limiti, *altro, **resto):
        viste.append(([f.id for g in gruppi for f in g.foto], limiti))
        return pianifica(snapshot, campagna_ai, gruppi, limiti, *altro, **resto)

    monkeypatch.setattr(ai, "pianifica_campagna", pianifica_e_guarda)

    _job(campagna.id)

    (foto_viste, limiti), *_ = viste
    attese = [ids[n] for n in (2, 3, 4, 5, 6, 7)]
    assert foto_viste == attese
    for limite in limiti.values():
        assert limite["foto_disponibili"] == attese
        assert (limite["foto_riempitivo"], limite["riempitivi"]) == ([], 0)


def test_un_post_e_una_foto_anche_se_il_provider_sa_fare_i_caroselli(db):
    """A8: nessun carosello, perché le foto del piano non avanzano mai."""
    with usa_ai(AIFinto(carosello=True)):
        campagna = _campagna(db, n_foto=8)

        _job(campagna.id)

    assert campagna.stato == "in_revisione"
    post = post_della_campagna(db, campagna.id)
    assert {p.formato for p in post} == {"singola"}
    assert all(len(_foto_del_post(p)) <= 1 for p in post)


def test_le_foto_usate_contano_i_loro_utilizzi(db, ai):
    campagna = _campagna(db, n_foto=5)

    _job(campagna.id)

    immagini = [
        f
        for f in campagne.foto_della_campagna(db, campagna.id)
        if f.origine == "caricata"
    ]
    # ogni foto esce una volta su Facebook e una su Instagram
    assert len(immagini) == 5
    assert [f.n_utilizzi for f in immagini] == [2] * 5
    assert all(f.analisi_ai["idonea"] is True for f in immagini)


def test_la_generazione_usa_la_fotografia_del_profilo(db, ai):
    """Costituzione §1.4: il nome nei testi è quello salvato all'invio."""
    campagna = _campagna(db)
    bottega = artigiani.profilo(db, campagna.profilo_id)
    bottega.nome = "Nome cambiato dopo l'invio"
    bottega.frequenza = "f5_piu"
    db.commit()

    _job(campagna.id)

    post = post_della_campagna(db, campagna.id)
    assert len(post) == 12  # 3 a settimana, come all'invio: non 5
    assert all("Ceramiche Bianchi" in p.versione_corrente.testo for p in post)


def test_un_canale_tolto_resta_fuori_dal_piano(db, ai):
    campagna = _campagna(db, canali_tolti=["facebook"])

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    post = post_della_campagna(db, campagna.id)
    assert {p.canale for p in post} == {"instagram"}
    assert len(post) == 6


# --- Stati in cui il job non fa nulla -----------------------------------------


@pytest.mark.parametrize("stato", ["bozza", "in_revisione", "attiva", "respinta"])
def test_fuori_da_inviata_e_in_generazione_il_job_non_fa_nulla(db, ai, stato):
    campagna = _campagna(db, stato=stato)

    assert _job(campagna.id) == 1

    assert campagna.stato == stato
    assert ai.chiamate == []
    assert post_della_campagna(db, campagna.id) == []
    assert _errori(db, campagna) == []


def test_le_tappe_in_ordine_un_passo_alla_volta(db, ai):
    campagna = _campagna(db, n_foto=4, canali=["instagram"])
    viste = []

    while True:
        viste.append(generazione.prossima_tappa(db, campagna))
        if not generazione.passo(db, campagna.id, ADESSO):
            break
        db.commit()

    assert viste == ["avvio", "analisi", "piano"] + ["testi"] * 6 + ["fine"]
    assert generazione.prossima_tappa(db, campagna) is None
    assert campagna.stato == "in_revisione"


# --- Analisi ------------------------------------------------------------------


def test_una_stella_gia_salvata_non_conta_piu(db, ai):
    """ADR-114, A11: 8 foto e 6 post, l'ultima ha `da_usare` e resta un doppione.

    La colonna resta nel database, ma la generazione non la legge: la foto non
    entra nel piano per forza e l'analisi dell'AI resta com'è.
    """
    campagna = _campagna(db, n_foto=8)
    ids = _foto_ids(db, campagna)
    con_stella, altra = ids[7], ids[0]
    campagne.foto_per_id(db, [con_stella])[0].da_usare = True
    db.commit()
    ai.comanda_analisi(con_stella, simile_a=altra)

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    immagini = {f.id: f for f in campagne.foto_della_campagna(db, campagna.id)}
    assert immagini[con_stella].analisi_ai["simile_a"] == altra
    assert immagini[altra].analisi_ai["simile_a"] is None
    usate = {f for p in post_della_campagna(db, campagna.id) for f in _foto_del_post(p)}
    assert con_stella not in usate


@pytest.mark.parametrize("tipo", ["richiesta", "rifiuto"])
def test_ca59_errore_su_una_sola_foto_la_foto_resta_fuori_con_il_motivo(db, ai, tipo):
    campagna = _campagna(db, n_foto=7)
    guasta = _foto_ids(db, campagna)[2]
    ai.comanda_errore("analizza_gruppo", tipo, volte=None, foto_id=guasta)

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    immagini = {f.id: f for f in campagne.foto_della_campagna(db, campagna.id)}
    assert immagini[guasta].analisi_ai["idonea"] is False
    assert "simulato" in immagini[guasta].analisi_ai["motivo"]
    usate = {f for p in post_della_campagna(db, campagna.id) for f in _foto_del_post(p)}
    assert guasta not in usate
    assert len(usate) == 6
    # un errore che non ferma l'esecuzione non si salva tra gli errori
    assert _errori(db, campagna) == []


def test_analisi_senza_esito_per_una_foto_e_un_errore_di_risposta(db, ai, monkeypatch):
    campagna = _campagna(db)
    monkeypatch.setattr(ai, "analizza_gruppo", lambda gruppo: {})

    assert jobs.esegui_generazione(campagna.id, 1) is True

    (errore,) = _errori(db, campagna)
    assert (errore.tipo, errore.tappa) == ("risposta", "analisi")


# --- Piano --------------------------------------------------------------------


def test_con_poche_foto_la_generazione_non_si_ferma(db, ai):
    """4 foto, 2 non idonee: 2 disponibili su 6 post chiesti, e si arriva in fondo.

    Dall'MVP il piano non è mai debole (ADR-114, A3): niente `piano_da_rivedere`.
    """
    campagna = _campagna(db, n_foto=4)
    ids = _foto_ids(db, campagna)
    ai.comanda_analisi(ids[2], idonea=False, motivo="Foto scura")
    ai.comanda_analisi(ids[3], idonea=False, motivo="Foto mossa")

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    assert piano_corrente(db, campagna.id).debole is False
    assert _notifiche(db, campagna, "piano_da_rivedere") == []
    for canale in DUE_CANALI:
        post = _post_del_canale(db, campagna, canale)
        assert [p.riempitivo for p in post] == [None] * 2 + ["immagine_ai"] * 4
        assert all(len(p.versioni) == 1 for p in post)


def test_piano_non_valido_si_fa_riscrivere(db, ai):
    """R-09: due piani non passano il controllo, il terzo sì."""
    campagna = _campagna(db)
    ai.comanda_piano_non_valido(2)

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    assert [c["riscrittura"] for c in _chiamate(ai, "pianifica_campagna")] == [
        False,
        True,
        True,
    ]
    assert piano_corrente(db, campagna.id).numero == 1


def test_piano_non_valido_dopo_tre_riscritture_e_un_errore_di_risposta(db, ai):
    campagna = _campagna(db)
    ai.comanda_piano_non_valido(4)

    assert jobs.esegui_generazione(campagna.id, 1) is True

    assert campagna.stato == "in_generazione"
    assert len(_chiamate(ai, "pianifica_campagna")) == 4
    assert piano_corrente(db, campagna.id) is None
    (errore,) = _errori(db, campagna)
    assert (errore.tipo, errore.tappa) == ("risposta", "piano")
    assert "dopo 3 riscritture" in errore.messaggio
    assert "i post devono essere 6" in errore.messaggio

    # la nuova esecuzione trova un'AI che risponde bene e arriva in fondo
    assert jobs.esegui_generazione(campagna.id, 2) is False
    assert campagna.stato == "in_revisione"
    assert len(_chiamate(ai, "analizza_gruppo")) == 1


# --- Archivio della bottega: congelato (ADR-114, A10) -------------------------


def _conclusa(db, campagna) -> list:
    """Le 4 foto, idonee, di una campagna conclusa della stessa bottega."""
    chiusa = campagna_conclusa(db, profilo_id=campagna.profilo_id)
    db.commit()
    return campagne.foto_della_campagna(db, chiusa.id)


def test_l_archivio_della_bottega_non_entra_nel_piano(db, ai):
    """Ogni foto che manca diventa un'immagine AI: nessuna foto d'archivio."""
    campagna = _campagna(db, n_foto=4, canali=["instagram"])
    nuove = _foto_ids(db, campagna)
    vecchie = _conclusa(db, campagna)
    mazzo = gruppo_di_archivio(db, profilo_id=campagna.profilo_id, n_foto=3)
    db.commit()

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    post = _post_del_canale(db, campagna, "instagram")
    assert [p.riempitivo for p in post] == [None] * 4 + ["immagine_ai"] * 2
    assert [_foto_del_post(p) for p in post[:4]] == [[n] for n in nuove]
    # i rimpiazzi hanno un'immagine AI, mai una foto dell'archivio
    creata = {f.id for f in campagne.foto_della_campagna(db, campagna.id)} - set(nuove)
    assert {tuple(_foto_del_post(p)) for p in post[4:]} == {(n,) for n in creata}
    assert len(creata) == 2
    # solo il gruppo della campagna si analizza: l'archivio resta com'è
    assert len(_chiamate(ai, "analizza_gruppo")) == 1
    assert all(f.n_utilizzi == 0 for f in vecchie + list(mazzo.foto))
    assert {uscita.gruppo_id for uscita in uscite_della_campagna(db, campagna.id)} <= {
        None,
        campagne.gruppi_della_campagna(db, campagna.id)[0].id,
    }


def test_ca50_riprova_non_rianalizza_le_foto_della_campagna(db, ai):
    campagna = _campagna(db, canali=["instagram"])
    ai.comanda_errore("pianifica_campagna", "temporaneo", volte=3)

    assert _job(campagna.id) == 3

    assert campagna.stato == "generazione_fallita"
    assert len(_chiamate(ai, "analizza_gruppo")) == 1

    _riprova(db, campagna)
    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    assert len(_chiamate(ai, "analizza_gruppo")) == 1


# --- Testi --------------------------------------------------------------------


def test_ca18_testo_con_un_blocco_dopo_tre_riscritture_il_post_e_da_rivedere(db, ai):
    campagna = _campagna(db)
    ai.comanda_testo(
        "Uno sconto garantito.", ["ceramica"], volte=None, canale="facebook"
    )

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    for post in _post_del_canale(db, campagna, "facebook"):
        assert post.da_rivedere is True
        versione = post.versione_corrente
        assert versione.testo == "Uno sconto garantito."
        assert {(e["regola"], e["livello"]) for e in versione.errori_validazione} == {
            ("parole_vietate", "blocco"),
            ("da_non_dire", "blocco"),
        }
    assert all(not p.da_rivedere for p in _post_del_canale(db, campagna, "instagram"))
    # 6 post, ognuno scritto una volta e riscritto tre
    su_facebook = [c for c in _chiamate(ai, "genera_post") if c["canale"] == "facebook"]
    assert len(su_facebook) == 24
    assert [c["riscrittura"] for c in su_facebook[:4]] == [False, True, True, True]


def test_ca18_testo_con_i_soli_avvisi_non_e_da_rivedere_e_gli_avvisi_si_salvano(db, ai):
    campagna = _campagna(db)
    lungo = ("Un vaso dipinto a mano. " * 30)[:650]  # oltre i 600 di Instagram
    ai.comanda_testo(lungo, ["ceramica"], volte=None, canale="instagram")

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    for post in _post_del_canale(db, campagna, "instagram"):
        assert post.da_rivedere is False
        assert [
            (e["regola"], e["livello"])
            for e in post.versione_corrente.errori_validazione
        ] == [("max_caratteri", "avviso")]


def test_testo_riscritto_bene_non_lascia_errori(db, ai):
    campagna = _campagna(db, canali=["instagram"])
    ai.comanda_testo("", volte=1)

    _job(campagna.id)

    post = post_della_campagna(db, campagna.id)
    assert all(not p.da_rivedere for p in post)
    assert all(p.versione_corrente.errori_validazione == [] for p in post)
    assert [c["riscrittura"] for c in _chiamate(ai, "genera_post")][:3] == [
        False,
        True,
        False,
    ]


@pytest.mark.parametrize("tipo", ["richiesta", "rifiuto"])
def test_errore_sul_testo_di_un_post_versione_vuota_con_un_blocco_e_si_continua(
    db, ai, tipo
):
    """R-35: `richiesta` o `rifiuto` sul testo non fermano la generazione."""
    campagna = _campagna(db, canali=["instagram"])
    ai.comanda_errore("genera_post", tipo, volte=1)

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    post = post_della_campagna(db, campagna.id)
    primo = post[0]
    assert primo.da_rivedere is True
    assert (primo.versione_corrente.testo, primo.versione_corrente.hashtag) == ("", [])
    assert primo.versione_corrente.provider_ai is None
    (blocco,) = primo.versione_corrente.errori_validazione
    assert (blocco["livello"], blocco["regola"]) == ("blocco", "testo_vuoto")
    assert "simulato" in blocco["messaggio"]
    assert len(_foto_del_post(primo)) == 1
    assert all(not p.da_rivedere for p in post[1:])
    assert _errori(db, campagna) == []


# --- Errori che fermano l'esecuzione (R-35) -------------------------------------


def test_ca19_errore_temporaneo_a_ogni_esecuzione_tre_esecuzioni_poi_fallita(db, ai):
    campagna = _campagna(db)
    ai.comanda_errore("genera_post", "temporaneo", volte=None, canale="instagram")

    assert _job(campagna.id) == 3

    assert campagna.stato == "generazione_fallita"
    errori = _errori(db, campagna)
    assert len(errori) == 3
    for errore in errori:
        assert (errore.tipo, errore.tappa, errore.canale) == (
            "temporaneo",
            "testi",
            "instagram",
        )
        assert "simulato" in errore.messaggio
    assert ultimo_errore(db, campagna.id).id == errori[-1].id

    # Riprova → inviata e riparte, senza rifare ciò che è già salvato
    scritti = len([p for p in post_della_campagna(db, campagna.id) if p.versioni])
    assert scritti >= 1
    with usa_ai(AIFinto()) as riparata:
        _riprova(db, campagna)
        assert campagna.stato == "inviata"
        assert _job(campagna.id) == 1
    assert campagna.stato == "in_revisione"
    assert _chiamate(riparata, "analizza_gruppo") == []
    assert _chiamate(riparata, "pianifica_campagna") == []
    assert len(_chiamate(riparata, "genera_post")) == 12 - scritti
    assert all(len(p.versioni) == 1 for p in post_della_campagna(db, campagna.id))


def test_ca50_riprova_dopo_l_analisi_non_rianalizza_le_foto(db, ai):
    campagna = _campagna(db)
    ai.comanda_errore("pianifica_campagna", "temporaneo", volte=3)

    assert _job(campagna.id) == 3

    assert campagna.stato == "generazione_fallita"
    assert ultimo_errore(db, campagna.id).tappa == "piano"
    assert len(_chiamate(ai, "analizza_gruppo")) == 1
    analizzate = {
        f.id: dict(f.analisi_ai) for f in campagne.foto_della_campagna(db, campagna.id)
    }
    assert all(analisi["idonea"] for analisi in analizzate.values())

    _riprova(db, campagna)
    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    assert len(_chiamate(ai, "analizza_gruppo")) == 1


def test_ca58_errore_di_configurazione_fallita_subito_senza_altre_esecuzioni(db, ai):
    campagna = _campagna(db)
    ai.comanda_errore("analizza_gruppo", "configurazione", volte=None)

    # la prima esecuzione non chiede di ripartire
    assert jobs.esegui_generazione(campagna.id, 1) is False

    assert campagna.stato == "generazione_fallita"
    (errore,) = _errori(db, campagna)
    assert (errore.tipo, errore.tappa, errore.canale) == (
        "configurazione",
        "analisi",
        None,
    )
    assert len(_chiamate(ai, "analizza_gruppo")) == 1


def test_ca58_litellm_senza_i_modelli_fallita_subito_con_il_motivo(db, monkeypatch):
    """`AI_PROVIDER=litellm` senza i modelli in `.env`: configurazione (converge §3)."""
    import app.adapters.ai.litellm as modulo_litellm

    campagna = _campagna(db)
    imposta_ai(None)
    senza_modelli = leggi_impostazioni().model_copy(
        update={
            "ai_provider": "litellm",
            "ai_modello_visione": "",
            "ai_modello_testo": "",
        }
    )
    monkeypatch.setattr(modulo_ai, "leggi_impostazioni", lambda: senza_modelli)
    monkeypatch.setattr(modulo_litellm, "leggi_impostazioni", lambda: senza_modelli)

    assert jobs.esegui_generazione(campagna.id, 1) is False

    assert campagna.stato == "generazione_fallita"
    errore = ultimo_errore(db, campagna.id)
    assert errore.tipo == "configurazione"
    assert "AI_MODELLO_VISIONE" in errore.messaggio


@pytest.mark.parametrize("tipo", ["temporaneo", "risposta", "richiesta", "rifiuto"])
def test_un_errore_che_passa_non_ferma_la_campagna(db, ai, tipo):
    """Un solo errore sul piano: la seconda esecuzione arriva in fondo."""
    campagna = _campagna(db)
    ai.comanda_errore("pianifica_campagna", tipo, volte=1)

    assert _job(campagna.id) == 2

    assert campagna.stato == "in_revisione"
    (errore,) = _errori(db, campagna)
    assert (errore.tipo, errore.tappa) == (tipo, "piano")


def test_errore_imprevisto_vale_come_temporaneo_e_non_lascia_la_campagna_ferma(
    db, ai, monkeypatch
):
    campagna = _campagna(db)

    def si_rompe(*args, **kwargs):
        raise RuntimeError("dati riservati di marta@example.com")

    monkeypatch.setattr(generazione, "valida_testo", si_rompe)

    assert _job(campagna.id) == 3

    assert campagna.stato == "generazione_fallita"
    errori = _errori(db, campagna)
    assert len(errori) == 3
    for errore in errori:
        assert (errore.tipo, errore.tappa, errore.canale) == (
            "temporaneo",
            "testi",
            None,
        )
        assert "RuntimeError" in errore.messaggio
        assert "marta" not in errore.messaggio


def test_cio_che_un_passo_ha_salvato_resta_se_quello_dopo_fallisce(db, ai):
    """R-24: l'errore annulla solo il post in corso, non quelli già scritti."""
    campagna = _campagna(db)
    ai.comanda_errore("genera_post", "temporaneo", volte=1, canale="instagram")

    assert jobs.esegui_generazione(campagna.id, 1) is True

    assert campagna.stato == "in_generazione"
    post = post_della_campagna(db, campagna.id)
    assert len(post) == 12
    scritti = [p for p in post if p.versioni]
    assert len(scritti) >= 1
    assert all(p.canale == "facebook" for p in scritti)
    assert piano_corrente(db, campagna.id) is not None

    assert jobs.esegui_generazione(campagna.id, 2) is False

    assert campagna.stato == "in_revisione"
    assert all(len(p.versioni) == 1 for p in post_della_campagna(db, campagna.id))
    assert len(_chiamate(ai, "pianifica_campagna")) == 1
    assert len(_chiamate(ai, "genera_post")) == 13  # 12 riusciti e quello fallito


def test_un_post_fallito_non_lascia_una_foto_senza_post(db, ai):
    """Nessuna foto nuova nasce se il testo di un post non si scrive."""
    campagna = _campagna(db, n_foto=4, canali=["instagram"])
    ai.comanda_errore("genera_post", "temporaneo", volte=None)

    assert _job(campagna.id) == 3

    assert campagna.stato == "generazione_fallita"
    immagini = campagne.foto_della_campagna(db, campagna.id)
    assert [f.origine for f in immagini] == ["caricata"] * 4


def test_errore_su_una_campagna_gia_uscita_dalla_generazione_non_cambia_lo_stato(
    db, ai
):
    campagna = _campagna(db, stato="in_revisione")

    assert generazione.registra_errore(db, campagna.id, RuntimeError("x"), 3) is False

    assert campagna.stato == "in_revisione"
    assert len(_errori(db, campagna)) == 1


# --- Il job nella coda ----------------------------------------------------------


def test_il_job_e_registrato_con_tre_esecuzioni_a_trenta_secondi():
    task = coda_app.tasks[GENERA_CAMPAGNA]

    assert task.pass_context is True
    # la prima esecuzione più due nuovi tentativi
    assert generazione.ESECUZIONI == 3
    assert task.retry_strategy.max_attempts == 2
    assert task.retry_strategy.wait == 30
    assert task.retry_strategy.retry_exceptions == [jobs.NuovaEsecuzione]


def test_il_job_accodato_per_nome_arriva_in_fondo(db, ai, coda, monkeypatch):
    """Come da /invia: accodato per nome, eseguito dal worker."""
    monkeypatch.setattr(coda_app.periodic_registry, "periodic_tasks", {})
    campagna = _campagna(db, canali=["instagram"])
    job_id = accoda(GENERA_CAMPAGNA, campagna_id=campagna.id)

    coda_app.run_worker(wait=False, install_signal_handlers=False, listen_notify=False)

    assert coda.jobs[job_id]["status"] == "succeeded"
    db.expire_all()
    assert campagne.campagna(db, campagna.id).stato == "in_revisione"


def test_il_job_che_fallisce_torna_in_coda_per_una_nuova_esecuzione(
    db, ai, coda, monkeypatch
):
    monkeypatch.setattr(coda_app.periodic_registry, "periodic_tasks", {})
    campagna = _campagna(db, canali=["instagram"])
    ai.comanda_errore("pianifica_campagna", "temporaneo", volte=None)
    job_id = accoda(GENERA_CAMPAGNA, campagna_id=campagna.id)
    prima = datetime.now(timezone.utc)

    coda_app.run_worker(wait=False, install_signal_handlers=False, listen_notify=False)

    job = coda.jobs[job_id]
    assert (job["status"], job["attempts"]) == ("todo", 1)
    assert job["scheduled_at"] - prima >= timedelta(seconds=29)
    db.expire_all()
    assert campagne.campagna(db, campagna.id).stato == "in_generazione"
    assert len(_errori(db, campagna)) == 1


def test_campagna_in_bozza_non_ha_job_da_fare(db, ai):
    campagna = campagna_in_bozza(db)
    db.commit()

    assert _job(campagna.id) == 1
    assert campagna.stato == "bozza"


# --- Notifiche della generazione (T2b-34, CA-55) ------------------------------


def _notifiche(db, campagna, tipo: str) -> list:
    """Le notifiche di un tipo scritte per la campagna."""
    from app.moduli.notifiche.models import Notifica

    return list(
        db.scalars(
            select(Notifica).where(
                Notifica.campagna_id == campagna.id, Notifica.tipo == tipo
            )
        )
    )


def test_ca55_campagna_pronta_avvisa_gli_operatori(db, ai):
    """Generazione arrivata in fondo → `in_revisione`, notifica `campagna_pronta`."""
    from tests.moduli.accesso.fabbrica import utente

    campagna = _campagna(db)
    operatore = utente(db, "operatore")
    admin = utente(db, "admin")

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    note = _notifiche(db, campagna, "campagna_pronta")
    assert {una.utente_id for una in note} == {operatore.id, admin.id}
    assert all(una.post_id is None for una in note)
    assert all(una.stato_invio == "da_inviare" for una in note)


def test_ca55_generazione_fallita_una_notifica_sola_per_evento(db, ai):
    """Tre esecuzioni fallite → `generazione_fallita`, una notifica; un altro
    giro dopo Riprova è lo stesso evento e non la ripete."""
    from tests.moduli.accesso.fabbrica import utente

    campagna = _campagna(db)
    operatore = utente(db, "operatore")
    ai.comanda_errore("pianifica_campagna", "temporaneo", volte=None)

    assert _job(campagna.id) == 3

    assert campagna.stato == "generazione_fallita"
    [notifica] = _notifiche(db, campagna, "generazione_fallita")
    assert notifica.utente_id == operatore.id

    _riprova(db, campagna)
    assert _job(campagna.id) == 3

    assert campagna.stato == "generazione_fallita"
    assert _notifiche(db, campagna, "generazione_fallita") == [notifica]


def test_ca55_un_errore_che_passa_non_manda_notifiche(db, ai):
    """Un'esecuzione che si riprende da sola non è un evento: niente notifica."""
    campagna = _campagna(db)
    ai.comanda_errore("pianifica_campagna", "temporaneo", volte=1)

    assert _job(campagna.id) == 2

    assert campagna.stato == "in_revisione"
    assert _notifiche(db, campagna, "generazione_fallita") == []


def test_ca108_ogni_foto_idonea_ha_il_riquadro_del_soggetto(db, ai):
    campagna = _campagna(db)

    _job(campagna.id)

    caricate = [
        f
        for f in campagne.foto_della_campagna(db, campagna.id)
        if f.origine == "caricata"
    ]
    assert caricate
    for foto in caricate:
        assert foto.analisi_ai["soggetto_box"] == {
            "x": 0.25,
            "y": 0.25,
            "larghezza": 0.5,
            "altezza": 0.5,
        }


@pytest.mark.parametrize(
    "riquadro",
    [{"x": 0.6, "y": 0.0, "larghezza": 0.6, "altezza": 0.5}, "centro", {"x": 0.1}],
)
def test_ca108_un_riquadro_fuori_da_0_1_o_malformato_vale_none_senza_errore(
    db, ai, riquadro
):
    campagna = _campagna(db)
    for foto_id in _foto_ids(db, campagna):
        ai.comanda_analisi(foto_id, soggetto_box=riquadro)

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    caricate = [
        f
        for f in campagne.foto_della_campagna(db, campagna.id)
        if f.origine == "caricata"
    ]
    assert all(f.analisi_ai["soggetto_box"] is None for f in caricate)
