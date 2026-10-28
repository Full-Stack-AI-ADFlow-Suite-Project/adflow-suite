"""T3-34: immagini AI di rimpiazzo dei post senza foto (spec R-28, R-43, R-44).

CA-57 con le immagini: il post `immagine_ai` ha la sua immagine quadrata e il
suo testo con «Immagine creata con AI». Una sola immagine per uscita, la stessa
su entrambi i canali; una nuova esecuzione non la ricrea; se il provider la
rifiuta, il post resta senza foto con un blocco e la generazione continua (R-35).
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO

import pytest
from PIL import Image
from sqlalchemy import select

from app.adapters.ai import AIFinto, ErroreAI, usa_ai
from app.adapters.archivio import ArchivioFinto, usa_archivio
from app.moduli.artigiani import service as artigiani
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import jobs
from app.moduli.contenuti.models import ChiamataAI, ErroreGenerazione, Post
from app.moduli.contenuti.service import accendi_intervento, post_della_campagna
from app.moduli.contenuti.validatore import LIMITE_CARATTERI, MAX_CARATTERI
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_inviata

INIZIO = date(2030, 1, 7)
FINE = date(2030, 1, 20)  # 6 post per canale
ADESSO = datetime(2030, 1, 1, 9, tzinfo=timezone.utc)
DICITURA = "Immagine creata con AI"


@pytest.fixture
def ai() -> Iterator[AIFinto]:
    with usa_ai(AIFinto()) as finto:
        yield finto


@pytest.fixture
def archivio() -> Iterator[ArchivioFinto]:
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


@pytest.fixture(autouse=True)
def transazioni_di_prova(db, archivio, monkeypatch) -> None:
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


def _campagna(db, *, canali=("facebook", "instagram")):
    """Campagna `inviata` con le 4 foto della fabbrica: 2 post per canale restano senza foto."""
    bottega = profilo(
        db,
        nome="Ceramiche Bianchi",
        citta="Deruta",
        tipo_prodotto="ceramica_vetro",
        tono=["caldo", "professionale"],
        canali=list(canali),
        frequenza="f3_4",
    )
    campagna = campagna_inviata(db, profilo_id=bottega.id, inizio=INIZIO, fine=FINE)
    db.commit()
    return campagna


def _job(campagna_id: int) -> int:
    for esecuzione in range(1, 4):
        if not jobs.esegui_generazione(campagna_id, esecuzione):
            return esecuzione
    raise AssertionError("Alla terza esecuzione il job non chiede di ripartire.")


def _rimpiazzi(db, campagna) -> list[Post]:
    return [
        p for p in post_della_campagna(db, campagna.id) if p.riempitivo == "immagine_ai"
    ]


def _foto_del_post(post: Post) -> list[int]:
    return [legame.foto_id for legame in post.versione_corrente.legami_foto]


def _foto_create(db, campagna):
    return [
        f
        for f in campagne.foto_della_campagna(db, campagna.id)
        if f.origine == "creata_ai"
    ]


def _chiamate(ai: AIFinto, operazione: str) -> list[dict]:
    return [c for c in ai.chiamate if c["operazione"] == operazione]


# --- L'immagine ----------------------------------------------------------------


def test_l_immagine_e_una_foto_creata_ai_senza_gruppo_salvata_nell_archivio(
    db, ai, archivio
):
    campagna = _campagna(db)

    _job(campagna.id)

    assert campagna.stato == "in_revisione"
    create = _foto_create(db, campagna)
    assert len(create) == 2
    for foto in create:
        assert foto.gruppo_id is None
        assert foto.profilo_id == campagna.profilo_id
        assert foto.mime == "image/png"
        assert foto.larghezza == foto.altezza
        assert foto.file in archivio.file_salvati
        with Image.open(BytesIO(archivio.leggi(foto.file))) as immagine:
            assert immagine.size == (foto.larghezza, foto.altezza)


def test_una_sola_immagine_per_uscita_la_stessa_su_entrambi_i_canali(db, ai):
    campagna = _campagna(db)

    _job(campagna.id)

    assert len(_chiamate(ai, "genera_immagine")) == 2
    per_uscita: dict[int, set[tuple[int, ...]]] = {}
    for post in _rimpiazzi(db, campagna):
        per_uscita.setdefault(post.uscita_id, set()).add(tuple(_foto_del_post(post)))
    assert len(per_uscita) == 2
    for versioni in per_uscita.values():
        assert len(versioni) == 1
        assert len(next(iter(versioni))) == 1
    create = {f.id for f in _foto_create(db, campagna)}
    assert {foto for v in per_uscita.values() for t in v for foto in t} == create


def test_un_canale_solo_ha_la_sua_immagine_per_ogni_rimpiazzo(db, ai):
    campagna = _campagna(db, canali=("instagram",))

    _job(campagna.id)

    assert len(_rimpiazzi(db, campagna)) == 2
    assert len(_foto_create(db, campagna)) == 2
    assert len(_chiamate(ai, "genera_immagine")) == 2


def test_il_prompt_parte_dal_profilo_dal_tema_e_dalla_stagione_del_post(db, ai):
    campagna = _campagna(db)

    _job(campagna.id)

    for chiamata in _chiamate(ai, "genera_immagine"):
        prompt = chiamata["prompt"]
        assert "bottega di ceramica e vetro a Deruta" in prompt
        assert "Stagione: inverno." in prompt
        assert "Tono: caldo, professionale." in prompt
        assert "nessuna persona riconoscibile" in prompt


def test_il_testo_di_un_rimpiazzo_riceve_cio_che_l_immagine_mostra(db, ai):
    """Il testo deve richiamare l'immagine AI: all'AI va il prompt che l'ha creata."""
    campagna = _campagna(db)

    _job(campagna.id)

    prompt = {c["prompt"] for c in _chiamate(ai, "genera_immagine")}
    testi = [c for c in _chiamate(ai, "genera_post") if c.get("immagine_ai")]
    assert testi
    assert all(c["immagine_ai"] in prompt for c in testi)


def test_il_prompt_usa_la_fotografia_del_profilo_non_il_profilo_corrente(db, ai):
    campagna = _campagna(db)
    artigiani.profilo(db, campagna.profilo_id).citta = "Altrove"
    db.commit()

    _job(campagna.id)

    assert all("Deruta" in c["prompt"] for c in _chiamate(ai, "genera_immagine"))


def test_una_nuova_esecuzione_non_ricrea_le_immagini_gia_fatte(db, ai, monkeypatch):
    """R-24: il testo di un rimpiazzo di Instagram fallisce, ma le immagini già salvate restano."""
    campagna = _campagna(db)
    vero = ai.genera_post
    fallimenti = []

    def genera_post(snapshot, campagna_ai, post, scheda, **altro):
        if post.riempitivo == "immagine_ai" and post.canale == "instagram":
            if not fallimenti:
                fallimenti.append(post.tema)
                raise ErroreAI("temporaneo", "Errore simulato.")
        return vero(snapshot, campagna_ai, post, scheda, **altro)

    monkeypatch.setattr(ai, "genera_post", genera_post)

    assert _job(campagna.id) == 2

    assert fallimenti
    assert campagna.stato == "in_revisione"
    assert len(_foto_create(db, campagna)) == 2
    assert len(_chiamate(ai, "genera_immagine")) == 2


def test_un_errore_temporaneo_dell_immagine_fa_ripartire_la_generazione(db, ai):
    campagna = _campagna(db)
    ai.comanda_errore("genera_immagine", "temporaneo", volte=1)

    assert _job(campagna.id) == 2

    assert campagna.stato == "in_revisione"
    assert len(_foto_create(db, campagna)) == 2


def test_un_errore_di_configurazione_ferma_la_generazione_con_la_tappa_immagini(db, ai):
    campagna = _campagna(db)
    ai.comanda_errore("genera_immagine", "configurazione", volte=None)

    assert _job(campagna.id) == 1

    assert campagna.stato == "generazione_fallita"
    errore = db.scalars(
        select(ErroreGenerazione).where(ErroreGenerazione.campagna_id == campagna.id)
    ).one()
    assert (errore.tipo, errore.tappa) == ("configurazione", "immagini")


# --- Dicitura -------------------------------------------------------------------


def test_il_testo_dei_rimpiazzi_porta_la_dicitura_in_fondo_gli_altri_no(db, ai):
    campagna = _campagna(db)

    _job(campagna.id)

    for post in post_della_campagna(db, campagna.id):
        testo = post.versione_corrente.testo
        if post.riempitivo == "immagine_ai":
            assert testo.endswith(f"\n\n{DICITURA}")
            assert testo.count(DICITURA) == 1
        else:
            assert DICITURA not in testo


def test_il_validatore_conta_la_dicitura_nei_caratteri(db, ai):
    """590 caratteri stanno nei 600 di Instagram; con la dicitura (24 in più) no."""
    ai.comanda_testo("a" * 590, ["vasi"], volte=None, canale="instagram")
    campagna = _campagna(db, canali=("instagram",))

    _job(campagna.id)

    for post in post_della_campagna(db, campagna.id):
        errori = post.versione_corrente.errori_validazione
        if post.riempitivo != "immagine_ai":
            assert errori == []
            assert len(post.versione_corrente.testo) == 590
        else:
            assert [e["regola"] for e in errori] == [MAX_CARATTERI]
            assert len(post.versione_corrente.testo) == 590 + 2 + len(DICITURA)
            assert not post.da_rivedere  # un avviso non ferma il post


def test_la_dicitura_resta_se_il_testo_ha_ancora_un_blocco(db, ai):
    ai.comanda_testo("a" * 2300, volte=None, canale="instagram")
    campagna = _campagna(db, canali=("instagram",))

    _job(campagna.id)

    primo = _rimpiazzi(db, campagna)[0]
    assert primo.da_rivedere
    assert primo.versione_corrente.testo.endswith(DICITURA)
    assert {e["regola"] for e in primo.versione_corrente.errori_validazione} == {
        LIMITE_CARATTERI
    }


def test_la_rigenerazione_del_testo_tiene_la_dicitura_e_la_stessa_immagine(db, ai):
    campagna = _campagna(db)
    _job(campagna.id)
    post = _rimpiazzi(db, campagna)[0]
    foto_prima = _foto_del_post(post)
    ai.comanda_testo("Un altro modo di dirlo.", volte=1)
    accendi_intervento(db, post.id, "rigenera_totale", ADESSO)
    db.commit()

    assert jobs.esegui_rigenerazione(post.id, None, None, 1) is False

    nuova = post_della_campagna(db, campagna.id)
    nuovo = next(p for p in nuova if p.id == post.id)
    assert nuovo.versione_corrente.numero == 2
    assert nuovo.versione_corrente.testo == f"Un altro modo di dirlo.\n\n{DICITURA}"
    assert _foto_del_post(nuovo) == foto_prima


# --- Costo ----------------------------------------------------------------------


def test_ogni_immagine_ha_la_sua_riga_di_costo(db):
    with usa_ai(AIFinto(costo_chiamata=Decimal("0.04"))):
        campagna = _campagna(db)

        _job(campagna.id)

    righe = list(
        db.scalars(
            select(ChiamataAI).where(
                ChiamataAI.campagna_id == campagna.id, ChiamataAI.tipo == "immagine"
            )
        )
    )
    assert len(righe) == 2
    assert all(r.n_immagini == 1 and r.post_id is not None for r in righe)
    assert {r.post_id for r in righe} <= {p.id for p in _rimpiazzi(db, campagna)}


# --- Errori sull'immagine (R-35) -------------------------------------------------


@pytest.mark.parametrize("tipo", ["richiesta", "rifiuto"])
def test_dopo_un_rifiuto_la_seconda_prova_usa_un_prompt_senza_tono_ne_stagione(
    db, ai, tipo
):
    campagna = _campagna(db)
    ai.comanda_errore("genera_immagine", tipo, volte=1)

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"
    prove = _chiamate(ai, "genera_immagine")
    assert len(prove) == 3  # due prove per la prima uscita, una per la seconda
    assert "Stagione" in prove[0]["prompt"] and "Tono" in prove[0]["prompt"]
    assert "Stagione" not in prove[1]["prompt"] and "Tono" not in prove[1]["prompt"]
    assert "Vincoli:" in prove[1]["prompt"]
    assert len(_foto_create(db, campagna)) == 2
    assert all(not p.da_rivedere for p in _rimpiazzi(db, campagna))


@pytest.mark.parametrize("tipo", ["richiesta", "rifiuto"])
def test_se_anche_la_seconda_prova_fallisce_il_post_resta_senza_foto_con_un_blocco(
    db, ai, tipo
):
    campagna = _campagna(db)
    ai.comanda_errore("genera_immagine", tipo, volte=None)

    assert _job(campagna.id) == 1

    assert campagna.stato == "in_revisione"  # la generazione continua
    rimpiazzi = _rimpiazzi(db, campagna)
    assert len(rimpiazzi) == 4
    for post in rimpiazzi:
        assert _foto_del_post(post) == []
        assert post.da_rivedere
        (blocco,) = post.versione_corrente.errori_validazione
        assert blocco["livello"] == "blocco"
        assert blocco["regola"] == "immagine_non_creata"
        assert blocco["messaggio"].startswith("Immagine non creata.")
        assert post.versione_corrente.testo  # il testo c'è
        assert DICITURA not in post.versione_corrente.testo
    assert _foto_create(db, campagna) == []
    # due prove per uscita, non per post: il secondo canale non riprova
    assert len(_chiamate(ai, "genera_immagine")) == 4


def test_la_rigenerazione_non_toglie_il_blocco_dell_immagine_che_manca(db, ai):
    campagna = _campagna(db)
    ai.comanda_errore("genera_immagine", "rifiuto", volte=None)
    _job(campagna.id)
    post = _rimpiazzi(db, campagna)[0]
    accendi_intervento(db, post.id, "rigenera_totale", ADESSO)
    db.commit()

    jobs.esegui_rigenerazione(post.id, None, None, 1)

    nuovo = next(p for p in post_della_campagna(db, campagna.id) if p.id == post.id)
    assert nuovo.versione_corrente.numero == 2
    assert nuovo.da_rivedere
    assert [e["regola"] for e in nuovo.versione_corrente.errori_validazione] == [
        "immagine_non_creata"
    ]
    assert DICITURA not in nuovo.versione_corrente.testo
