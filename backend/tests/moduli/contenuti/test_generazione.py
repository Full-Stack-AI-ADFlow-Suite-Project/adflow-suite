"""T1-34: job `genera_campagna` a tappe (plan §4, spec §2.2, R-24, R-35).

CA-17, CA-18, CA-19 (fino a `generazione_fallita`), CA-20, CA-49 (fino a
`piano_da_rivedere`), CA-50, CA-51, CA-52 (post con più foto), CA-57 (fino ai
post `da_approvare`), CA-58, CA-59; poi la ripresa dalle tappe già salvate e
gli errori tecnici secondo il tipo.
"""

from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image
from sqlalchemy import select

import app.adapters.ai as modulo_ai
from app.adapters.ai import AIFinto, imposta_ai, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
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


@pytest.fixture
def ai() -> Iterator[AIFinto]:
    with usa_ai(AIFinto()) as finto:
        yield finto


@pytest.fixture(autouse=True)
def archivio() -> Iterator[ArchivioFinto]:
    """Le cartoline vanno in un archivio in memoria: nessun file sul disco."""
    with usa_archivio(ArchivioFinto()) as finto:
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


def _campagna(db, *, n_foto: int = 6, canali=DUE_CANALI, stelle=(), **campi):
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
    immagini = campagne.foto_della_campagna(db, campagna.id)
    for posizione in stelle:
        immagini[posizione].da_usare = True
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


def test_ca17_sei_uscite_sei_post_per_canale_cinque_foto_e_una_cartolina(db, ai):
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
        assert [p.riempitivo for p in post] == [None] * 5 + ["cartolina"]
        con_foto = [_foto_del_post(p) for p in post[:5]]
        assert all(len(foto_del_post) == 1 for foto_del_post in con_foto)
        usate = [foto_del_post[0] for foto_del_post in con_foto]
        # nessuna foto due volte sullo stesso canale, tutte tra quelle caricate
        assert len(set(usate)) == 5
        assert set(usate) == caricate
    assert uscite[5].gruppo_id is None
    assert uscite[0].gruppo_id is not None


def test_ca57_i_post_che_mancano_sono_cartoline_con_immagine_e_testo(db, ai, archivio):
    """4 foto e 6 post chiesti: 2 cartoline per canale, nessun carosello."""
    ai.carosello = True  # anche se chiesto: su un canale con riempitivi non si fa
    campagna = _campagna(db, n_foto=4)
    caricate = set(_foto_ids(db, campagna))

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    assert piano_corrente(db, campagna.id).debole is False
    tutte = {f.id: f for f in campagne.foto_della_campagna(db, campagna.id)}
    immagini_delle_cartoline = []
    for canale in DUE_CANALI:
        post = _post_del_canale(db, campagna, canale)
        assert len(post) == 6
        assert {p.formato for p in post} == {"singola"}
        assert [p.riempitivo for p in post] == [None] * 4 + ["cartolina"] * 2
        assert all(p.stato == "da_approvare" for p in post)
        for cartolina in post[4:]:
            (foto_id,) = _foto_del_post(cartolina)
            immagine = tutte[foto_id]
            assert foto_id not in caricate
            assert (immagine.origine, immagine.gruppo_id) == ("cartolina", None)
            assert (immagine.larghezza, immagine.altezza) == (1080, 1080)
            aperta = Image.open(BytesIO(archivio.leggi(immagine.file)))
            assert (aperta.format, aperta.size) == ("PNG", (1080, 1080))
            assert cartolina.versione_corrente.testo
            assert cartolina.da_rivedere is False
            immagini_delle_cartoline.append(foto_id)
    # ogni cartolina ha la sua immagine
    assert len(set(immagini_delle_cartoline)) == 4
    assert len(archivio.file_salvati) == 4


def test_ca52_piano_con_un_carosello_post_con_piu_foto_in_ordine(db):
    with usa_ai(AIFinto(carosello=True)):
        campagna = _campagna(db, n_foto=8)
        ids = _foto_ids(db, campagna)

        _job(campagna.id)

    assert campagna.stato == "in_revisione"
    for canale in DUE_CANALI:
        primo = _post_del_canale(db, campagna, canale)[0]
        assert primo.formato == "carosello"
        legami = primo.versione_corrente.legami_foto
        assert [legame.posizione for legame in legami] == [1, 2]
        assert [legame.foto_id for legame in legami] == [ids[0], ids[6]]


def test_le_foto_usate_contano_i_loro_utilizzi(db, ai):
    campagna = _campagna(db, n_foto=5)

    _job(campagna.id)

    immagini = campagne.foto_della_campagna(db, campagna.id)
    caricate = [f for f in immagini if f.origine == "caricata"]
    cartoline = [f for f in immagini if f.origine == "cartolina"]
    # ogni foto esce una volta su Facebook e una su Instagram
    assert [f.n_utilizzi for f in caricate] == [2] * 5
    assert [f.n_utilizzi for f in cartoline] == [1, 1]
    assert all(f.analisi_ai["idonea"] is True for f in caricate)


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
        viste.append(generazione.prossima_tappa(db, campagna, ADESSO))
        if not generazione.passo(db, campagna.id, ADESSO):
            break
        db.commit()

    assert viste == ["avvio", "analisi", "piano"] + ["testi"] * 6 + ["fine"]
    assert generazione.prossima_tappa(db, campagna, ADESSO) is None
    assert campagna.stato == "in_revisione"


# --- Analisi ------------------------------------------------------------------


def test_ca51_la_foto_con_la_stella_e_nel_piano(db, ai):
    """8 foto e 6 post per canale: la stella è l'ultima, ma entra nel piano."""
    campagna = _campagna(db, n_foto=8, stelle=[7])
    con_stella = _foto_ids(db, campagna)[7]

    _job(campagna.id)

    for canale in DUE_CANALI:
        usate = [
            f for p in _post_del_canale(db, campagna, canale) for f in _foto_del_post(p)
        ]
        assert con_stella in usate


def test_ca51_la_foto_con_la_stella_non_idonea_resta_fuori_con_il_motivo(db, ai):
    campagna = _campagna(db, n_foto=8, stelle=[7])
    con_stella = _foto_ids(db, campagna)[7]
    ai.comanda_analisi(con_stella, idonea=False, motivo="Foto sfocata")

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    usate = {f for p in post_della_campagna(db, campagna.id) for f in _foto_del_post(p)}
    assert con_stella not in usate
    immagini = {f.id: f for f in campagne.foto_della_campagna(db, campagna.id)}
    assert immagini[con_stella].analisi_ai["idonea"] is False
    assert immagini[con_stella].analisi_ai["motivo"] == "Foto sfocata"


def test_ca51_tra_due_foto_quasi_uguali_il_doppione_e_quella_senza_stella(db, ai):
    campagna = _campagna(db, n_foto=8, stelle=[7])
    ids = _foto_ids(db, campagna)
    con_stella, altra = ids[7], ids[0]
    ai.comanda_analisi(con_stella, simile_a=altra)

    _job(campagna.id)

    immagini = {f.id: f for f in campagne.foto_della_campagna(db, campagna.id)}
    assert immagini[con_stella].analisi_ai["simile_a"] is None
    assert immagini[altra].analisi_ai["simile_a"] == con_stella
    usate = {f for p in post_della_campagna(db, campagna.id) for f in _foto_del_post(p)}
    assert con_stella in usate
    assert altra not in usate


def test_due_foto_con_la_stella_quasi_uguali_restano_tutte_e_due(db, ai):
    campagna = _campagna(db, n_foto=8, stelle=[6, 7])
    ids = _foto_ids(db, campagna)
    ai.comanda_analisi(ids[7], simile_a=ids[6])

    _job(campagna.id)

    immagini = {f.id: f for f in campagne.foto_della_campagna(db, campagna.id)}
    assert immagini[ids[6]].analisi_ai["simile_a"] is None
    assert immagini[ids[7]].analisi_ai["simile_a"] is None


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


def test_ca49_piano_debole_la_campagna_si_ferma_senza_testi_poi_prosegue(db, ai):
    """4 foto, 2 non idonee: 2 disponibili su 6 post chiesti, sotto la metà."""
    campagna = _campagna(db, n_foto=4)
    ids = _foto_ids(db, campagna)
    ai.comanda_analisi(ids[2], idonea=False, motivo="Foto scura")
    ai.comanda_analisi(ids[3], idonea=False, motivo="Foto mossa")

    assert _job(campagna.id) == 1

    assert campagna.stato == "piano_da_rivedere"
    assert piano_corrente(db, campagna.id).debole is True
    post = post_della_campagna(db, campagna.id)
    # il piano ha già i post chiesti, con i riempitivi; nessun testo generato
    assert Counter(p.canale for p in post) == {"facebook": 6, "instagram": 6}
    assert all(p.versioni == [] for p in post)
    assert _chiamate(ai, "genera_post") == []

    # Prosegui (in `revisione`): la campagna torna `in_generazione` e il job riparte
    campagne.cambia_stato(db, campagna, "in_generazione")
    db.commit()
    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    assert len(_chiamate(ai, "pianifica_campagna")) == 1  # il piano non si rifà
    assert len(_chiamate(ai, "analizza_gruppo")) == 1
    for canale in DUE_CANALI:
        post = _post_del_canale(db, campagna, canale)
        assert [p.riempitivo for p in post] == [None] * 2 + ["cartolina"] * 4
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


# --- Archivio della bottega (T2a-31, R-05, R-27, R-28) ------------------------


def _conclusa(db, campagna) -> list:
    """Le 4 foto, idonee, di una campagna conclusa della stessa bottega."""
    chiusa = campagna_conclusa(db, profilo_id=campagna.profilo_id)
    db.commit()
    return campagne.foto_della_campagna(db, chiusa.id)


def _uscita_da(immagine, **giorni_per_canale: int) -> None:
    """Scrive sulla foto che è uscita su quei canali, tanti giorni fa."""
    immagine.pubblicata_su = {
        canale: (ADESSO - timedelta(days=giorni)).isoformat()
        for canale, giorni in giorni_per_canale.items()
    }


def _foto_dei_post(db, campagna, canale: str) -> list[list[int]]:
    return [_foto_del_post(p) for p in _post_del_canale(db, campagna, canale)]


def test_ca76_archivio_mai_uscita_disponibile_recente_fuori_vecchia_riempitivo(db, ai):
    """4 foto nuove e 6 post per canale: il resto arriva dall'archivio."""
    campagna = _campagna(db, n_foto=4)
    nuove = _foto_ids(db, campagna)
    mai_su_instagram, recente, mai_uscita, recente_ovunque = _conclusa(db, campagna)
    _uscita_da(mai_su_instagram, facebook=91)  # su Facebook da più di 90 giorni
    _uscita_da(recente, facebook=31)
    _uscita_da(recente_ovunque, facebook=31, instagram=31)
    db.commit()

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    assert piano_corrente(db, campagna.id).debole is False
    # Facebook: 5 foto disponibili; il sesto post è la foto uscita lì 91 giorni fa
    facebook = _post_del_canale(db, campagna, "facebook")
    assert [p.riempitivo for p in facebook] == [None] * 5 + ["archivio"]
    assert _foto_dei_post(db, campagna, "facebook") == [[n] for n in nuove] + [
        [mai_uscita.id],
        [mai_su_instagram.id],
    ]
    # Instagram: le foto mai uscite lì bastano, nessun riempitivo
    instagram = _post_del_canale(db, campagna, "instagram")
    assert [p.riempitivo for p in instagram] == [None] * 6
    assert _foto_dei_post(db, campagna, "instagram") == [[n] for n in nuove] + [
        [mai_su_instagram.id],
        [recente.id],
    ]
    assert {p.formato for p in facebook + instagram} == {"singola"}
    assert all(p.versione_corrente.testo for p in facebook + instagram)
    # una foto uscita da meno di 90 giorni lì non compare
    usate_su_facebook = {
        f
        for foto_del_post in _foto_dei_post(db, campagna, "facebook")
        for f in foto_del_post
    }
    assert recente.id not in usate_su_facebook
    usate = {f for p in facebook + instagram for f in _foto_del_post(p)}
    assert recente_ovunque.id not in usate
    # le foto d'archivio contano i loro utilizzi, come le altre
    assert (mai_su_instagram.n_utilizzi, recente.n_utilizzi) == (2, 1)
    assert (mai_uscita.n_utilizzi, recente_ovunque.n_utilizzi) == (1, 0)
    # nessuna cartolina: la campagna non ha foto sue oltre a quelle caricate
    proprie = campagne.foto_della_campagna(db, campagna.id)
    assert [f.origine for f in proprie] == ["caricata"] * 4


def test_ca76_riempitivi_prima_la_foto_d_archivio_poi_la_cartolina(db, ai):
    """Una sola foto già uscita da più di 90 giorni e 2 post che mancano."""
    campagna = _campagna(db, n_foto=4)
    nuove = _foto_ids(db, campagna)
    vecchia, *recenti = _conclusa(db, campagna)
    _uscita_da(vecchia, facebook=120, instagram=95)
    for recente in recenti:
        _uscita_da(recente, facebook=10, instagram=89)
    db.commit()

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    proprie = {f.id: f for f in campagne.foto_della_campagna(db, campagna.id)}
    for canale in DUE_CANALI:
        post = _post_del_canale(db, campagna, canale)
        assert [p.riempitivo for p in post] == [None] * 4 + ["archivio", "cartolina"]
        usate = [f for p in post for f in _foto_del_post(p)]
        assert usate[:5] == nuove + [vecchia.id]
        assert proprie[usate[5]].origine == "cartolina"
        # nessuna foto due volte sullo stesso canale (costituzione §1.9)
        assert len(set(usate)) == 6
    uscite = uscite_della_campagna(db, campagna.id)
    assert uscite[4].gruppo_id == vecchia.gruppo_id
    assert uscite[5].gruppo_id is None


def test_i_gruppi_d_archivio_senza_analisi_si_analizzano_prima_del_piano(
    db, ai, monkeypatch
):
    """Foto caricate dal profilo, mai analizzate: l'analisi è una tappa (R-24)."""
    campagna = _campagna(db, n_foto=4, canali=["instagram"])
    mazzo = gruppo_di_archivio(db, profilo_id=campagna.profilo_id, n_foto=1)
    nuova = foto(db, gruppo=mazzo)
    scura = foto(db, gruppo=mazzo)
    db.commit()
    (gia_analizzata,) = [f.id for f in mazzo.foto if f.id not in (nuova.id, scura.id)]
    ai.comanda_analisi(scura.id, idonea=False, motivo="Foto scura")
    descrizioni = []
    scrivi = ai.genera_post

    def genera_post(snapshot, campagna_ai, post, scheda, **altro):
        descrizioni.append(post.descrizione_gruppo)
        return scrivi(snapshot, campagna_ai, post, scheda, **altro)

    monkeypatch.setattr(ai, "genera_post", genera_post)

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    # un'analisi per il gruppo della campagna e una per quello d'archivio,
    # con le sole foto che non l'avevano
    analisi = _chiamate(ai, "analizza_gruppo")
    assert len(analisi) == 2
    assert (analisi[1]["gruppo"], analisi[1]["foto"]) == (
        mazzo.id,
        [nuova.id, scura.id],
    )
    assert nuova.analisi_ai["idonea"] is True
    assert (scura.analisi_ai["idonea"], scura.analisi_ai["motivo"]) == (
        False,
        "Foto scura",
    )
    post = _post_del_canale(db, campagna, "instagram")
    assert [p.riempitivo for p in post] == [None] * 6
    assert [_foto_del_post(p) for p in post][4:] == [[gia_analizzata], [nuova.id]]
    # tema e descrizione dei post con una foto d'archivio sono quelli del suo gruppo
    assert uscite_della_campagna(db, campagna.id)[4].tema == mazzo.descrizione
    assert descrizioni == ["Gruppo di prova"] * 4 + [mazzo.descrizione] * 2


def test_ca50_riprova_non_rianalizza_le_foto_d_archivio(db, ai):
    campagna = _campagna(db, canali=["instagram"])
    mazzo = gruppo_di_archivio(db, profilo_id=campagna.profilo_id, n_foto=0)
    foto(db, gruppo=mazzo)
    db.commit()
    ai.comanda_errore("pianifica_campagna", "temporaneo", volte=3)

    assert _job(campagna.id) == 3

    assert campagna.stato == "generazione_fallita"
    assert len(_chiamate(ai, "analizza_gruppo")) == 2

    _riprova(db, campagna)
    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    assert len(_chiamate(ai, "analizza_gruppo")) == 2


def test_una_foto_arrivata_in_archivio_dopo_il_piano_non_si_analizza(db, ai):
    """Il piano è già salvato: la foto servirà alla prossima campagna."""
    campagna = _campagna(db, n_foto=4, canali=["instagram"])
    ai.comanda_errore("genera_post", "temporaneo", volte=1)
    assert jobs.esegui_generazione(campagna.id, 1) is True
    assert piano_corrente(db, campagna.id) is not None
    mazzo = gruppo_di_archivio(db, profilo_id=campagna.profilo_id, n_foto=0)
    tardiva = foto(db, gruppo=mazzo)
    db.commit()

    assert jobs.esegui_generazione(campagna.id, 2) is False

    assert campagna.stato == "in_revisione"
    assert len(_chiamate(ai, "analizza_gruppo")) == 1
    assert tardiva.analisi_ai is None
    post = _post_del_canale(db, campagna, "instagram")
    assert [p.riempitivo for p in post] == [None] * 4 + ["cartolina"] * 2


def test_errore_imprevisto_nell_analisi_dell_archivio_ha_la_tappa_analisi(
    db, ai, monkeypatch
):
    campagna = _campagna(db, canali=["instagram"])
    mazzo = gruppo_di_archivio(db, profilo_id=campagna.profilo_id, n_foto=0)
    foto(db, gruppo=mazzo)
    db.commit()
    analizza = ai.analizza_gruppo

    def si_rompe_con_l_archivio(gruppo):
        if gruppo.archivio:
            raise RuntimeError("x")
        return analizza(gruppo)

    monkeypatch.setattr(ai, "analizza_gruppo", si_rompe_con_l_archivio)

    assert jobs.esegui_generazione(campagna.id, 1) is True

    (errore,) = _errori(db, campagna)
    assert (errore.tipo, errore.tappa) == ("temporaneo", "analisi")


def test_piano_non_debole_grazie_alle_foto_d_archivio(db, ai):
    """Come CA-49, ma l'archivio porta le foto disponibili alla metà dei post."""
    campagna = _campagna(db, n_foto=4, canali=["instagram"])
    ids = _foto_ids(db, campagna)
    ai.comanda_analisi(ids[2], idonea=False, motivo="Foto scura")
    ai.comanda_analisi(ids[3], idonea=False, motivo="Foto mossa")
    gruppo_di_archivio(db, profilo_id=campagna.profilo_id, n_foto=1)
    db.commit()

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    assert piano_corrente(db, campagna.id).debole is False
    post = _post_del_canale(db, campagna, "instagram")
    assert [p.riempitivo for p in post] == [None] * 3 + ["cartolina"] * 3


def test_l_archivio_di_un_altra_bottega_non_entra_nel_piano(db, ai):
    campagna = _campagna(db, n_foto=4, canali=["instagram"])
    gruppo_di_archivio(db, n_foto=3)
    db.commit()

    _job(campagna.id)

    post = _post_del_canale(db, campagna, "instagram")
    assert [p.riempitivo for p in post] == [None] * 4 + ["cartolina"] * 2
    assert len(_chiamate(ai, "analizza_gruppo")) == 1


def test_la_stella_di_una_campagna_chiusa_non_vale_per_quella_nuova(db, ai):
    """6 foto nuove per 6 post: la foto d'archivio con la stella non ne toglie una."""
    campagna = _campagna(db, n_foto=6, canali=["instagram"])
    nuove = _foto_ids(db, campagna)
    vecchie = _conclusa(db, campagna)
    vecchie[0].da_usare = True
    db.commit()

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    assert _foto_dei_post(db, campagna, "instagram") == [[n] for n in nuove]


def test_un_canale_tolto_non_guarda_il_suo_archivio(db, ai):
    campagna = _campagna(db, n_foto=4, canali_tolti=["facebook"])
    vecchia, *_ = _conclusa(db, campagna)
    _uscita_da(vecchia, facebook=200)
    db.commit()

    _job(campagna.id)

    post = post_della_campagna(db, campagna.id)
    assert {p.canale for p in post} == {"instagram"}
    assert {p.riempitivo for p in post} == {None}


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


def test_ca58_provider_non_disponibile_fallita_subito_con_il_motivo(db, monkeypatch):
    """`AI_PROVIDER=litellm`: il provider vero non c'è ancora (converge §3, passo 6)."""
    campagna = _campagna(db)
    imposta_ai(None)
    monkeypatch.setattr(
        modulo_ai, "leggi_impostazioni", lambda: SimpleNamespace(ai_provider="litellm")
    )

    assert jobs.esegui_generazione(campagna.id, 1) is False

    assert campagna.stato == "generazione_fallita"
    errore = ultimo_errore(db, campagna.id)
    assert errore.tipo == "configurazione"
    assert "litellm" in errore.messaggio


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


def test_la_cartolina_di_un_post_fallito_non_lascia_una_foto_senza_post(db, ai):
    """La foto della cartolina nasce nella transazione del suo post."""
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
