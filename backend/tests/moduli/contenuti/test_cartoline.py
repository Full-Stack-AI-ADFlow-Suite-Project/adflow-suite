"""T1-35 e T2a-32: cartoline dei post riempitivo (spec R-28, R-40).

- Misura e formato del file.
- La foto creata: senza gruppo, con origine `cartolina`.
- Nessun file fuori dall'archivio di prova.
- CA-77 (cartolina): il logo è quello dello snapshot, sopra il nome.
"""

from io import BytesIO

import pytest
from PIL import Image

from app.adapters.archivio import ArchivioDisco, ArchivioFinto, usa_archivio
from app.moduli.campagne import service as campagne
from app.moduli.contenuti import cartoline
from app.moduli.contenuti.cartoline import componi_cartolina, disegna_cartolina
from tests.moduli.artigiani.fabbrica import profilo
from tests.moduli.campagne.fabbrica import campagna_inviata

NOME = "Ceramiche Bianchi"
TEMA = "Dietro ogni pezzo c'è una storia"
SFONDO = (245, 240, 232)
ROSSO = (200, 30, 30)
BLU = (30, 60, 200)
# Con tema e nome il logo sta in questo riquadro, largo 320 e alto 160 px.
RIQUADRO_DEL_LOGO = (380, 674, 700, 834)


def _logo(formato: str = "PNG", misura=(600, 300), colore=ROSSO) -> bytes:
    """Il file di un logo a tinta unita, come lo salva il profilo (R-40)."""
    file = BytesIO()
    Image.new("RGB", misura, colore).save(file, format=formato, quality=95)
    return file.getvalue()


def _apri(contenuto: bytes) -> Image.Image:
    immagine = Image.open(BytesIO(contenuto))
    immagine.load()
    return immagine


def _colori_diversi_dallo_sfondo(immagine: Image.Image, riquadro) -> int:
    ritaglio = immagine.convert("RGB").crop(riquadro)
    colori = ritaglio.getcolors(maxcolors=ritaglio.width * ritaglio.height)
    return sum(quanti for quanti, colore in colori if colore != SFONDO)


@pytest.fixture
def archivio():
    """Archivio di prova in memoria: nessun file sul disco."""
    with usa_archivio(ArchivioFinto()) as finto:
        yield finto


# --- Il file ------------------------------------------------------------------


def test_misura_e_formato_del_file():
    """R-28: immagine di 1080 × 1080 px; qui un PNG."""
    contenuto = disegna_cartolina(NOME, TEMA)
    immagine = _apri(contenuto)

    assert immagine.format == "PNG"
    assert immagine.size == (1080, 1080)
    assert contenuto.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(contenuto) < 10 * 1024 * 1024  # il limite di una foto (R-13)
    assert (cartoline.LATO, cartoline.MIME) == (1080, "image/png")


def test_la_cartolina_porta_il_tema_e_il_nome_della_bottega():
    """Il tema sta al centro, il nome in basso: lì l'immagine non è vuota."""
    immagine = _apri(disegna_cartolina(NOME, TEMA))
    centro = (150, 350, 930, 650)
    basso = (150, 830, 930, 950)

    assert _colori_diversi_dallo_sfondo(immagine, centro) > 500
    assert _colori_diversi_dallo_sfondo(immagine, basso) > 200
    # senza il nome la fascia in basso resta vuota
    solo_tema = _apri(disegna_cartolina(None, TEMA))
    assert _colori_diversi_dallo_sfondo(solo_tema, basso) == 0


def test_stessa_cartolina_a_parita_di_testi():
    assert disegna_cartolina(NOME, TEMA) == disegna_cartolina(NOME, TEMA)
    assert disegna_cartolina(NOME, TEMA) != disegna_cartolina(NOME, "Fatto a mano")
    assert disegna_cartolina(NOME, TEMA) != disegna_cartolina("Altra bottega", TEMA)


@pytest.mark.parametrize(
    ("nome", "tema"),
    [
        (NOME, "Perché è così: più qualità, città e caffè"),  # accenti
        (NOME, "parola " * 200),  # tema lunghissimo
        (NOME, "Supercalifragilistichespiralidoso" * 6),  # una parola senza spazi
        ("Bottega " * 40, TEMA),  # nome lunghissimo
        (NOME, ""),
        (NOME, None),
        ("", TEMA),
        (None, TEMA),
        (None, None),
        (NOME, "  tema\ncon   a capo\te spazi  "),
    ],
)
def test_testi_difficili_danno_comunque_una_cartolina(nome, tema):
    immagine = _apri(disegna_cartolina(nome, tema))

    assert immagine.format == "PNG"
    assert immagine.size == (1080, 1080)


@pytest.mark.parametrize("lettera", list("àèéìòùÀÈÉÌÒÙ€’«»…"))
def test_il_carattere_ha_le_lettere_dell_italiano(lettera):
    """Con il carattere incluso in Pillow «è» usciva come un quadratino vuoto."""
    assert cartoline._si_disegna(lettera)
    assert cartoline._pulito(f"caff{lettera}") == f"caff{lettera}"


def test_una_lettera_che_il_carattere_non_ha_non_diventa_un_quadratino(monkeypatch):
    """Un'emoji si toglie; una lettera con un segno che manca resta senza segno."""
    assert not cartoline._si_disegna("🎨")
    assert cartoline._pulito("Colori 🎨 e forme") == "Colori e forme"
    assert disegna_cartolina(NOME, "Colori 🎨 e forme") == disegna_cartolina(
        NOME, "Colori e forme"
    )

    vero = cartoline._si_disegna
    monkeypatch.setattr(cartoline, "_si_disegna", lambda l: l != "è" and vero(l))
    assert cartoline._pulito("caffè") == "caffe"


def test_il_font_sta_nel_modulo_con_la_sua_licenza():
    cartella = cartoline._FONT.parent
    assert cartoline._FONT.is_file()
    assert "SIL OPEN FONT LICENSE" in (cartella / "OFL.txt").read_text("utf-8")


def test_un_tema_lungo_resta_dentro_i_margini():
    """Niente testo sul bordo: la cornice e i margini restano puliti."""
    immagine = _apri(disegna_cartolina(NOME, "parola " * 200))

    for fascia in [(0, 0, 1080, 50), (0, 1030, 1080, 1080), (0, 0, 50, 1080)]:
        assert _colori_diversi_dallo_sfondo(immagine, fascia) == 0
    # tra la cornice e il margine del testo, a sinistra
    assert _colori_diversi_dallo_sfondo(immagine, (60, 60, 104, 1020)) == 0


# --- Il logo ------------------------------------------------------------------


def test_ca77_la_cartolina_porta_il_logo_sopra_il_nome():
    immagine = _apri(disegna_cartolina(NOME, TEMA, _logo())).convert("RGB")
    sinistra, alto, destra, basso = RIQUADRO_DEL_LOGO

    # il logo riempie il suo riquadro, centrato, e fuori non c'è
    for punto in [(sinistra, alto), (destra - 1, basso - 1), (540, 754)]:
        assert immagine.getpixel(punto) == ROSSO
    assert immagine.getpixel((sinistra - 1, 754)) == SFONDO
    assert immagine.getpixel((destra, 754)) == SFONDO
    # sotto il logo c'è il nome, sopra il tema: tra loro e il logo resta spazio
    assert _colori_diversi_dallo_sfondo(immagine, (150, 862, 930, 950)) > 200
    assert _colori_diversi_dallo_sfondo(immagine, (150, 108, 930, 634)) > 500
    assert _colori_diversi_dallo_sfondo(immagine, (150, 634, 930, alto)) == 0
    assert _colori_diversi_dallo_sfondo(immagine, (150, basso, 930, 862)) == 0


def test_senza_logo_la_cartolina_e_quella_di_sempre():
    assert disegna_cartolina(NOME, TEMA, None) == disegna_cartolina(NOME, TEMA)
    assert disegna_cartolina(NOME, TEMA, b"") == disegna_cartolina(NOME, TEMA)
    assert disegna_cartolina(NOME, TEMA, _logo()) != disegna_cartolina(NOME, TEMA)


def test_stessa_cartolina_a_parita_di_logo():
    assert disegna_cartolina(NOME, TEMA, _logo()) == disegna_cartolina(
        NOME, TEMA, _logo()
    )
    assert disegna_cartolina(NOME, TEMA, _logo()) != disegna_cartolina(
        NOME, TEMA, _logo(colore=BLU)
    )


@pytest.mark.parametrize(
    "logo",
    [
        b"non sono un'immagine",
        b"%PDF-1.7",
        _logo()[:60],  # un PNG troncato
        _logo("JPEG")[:80],
    ],
)
def test_un_logo_che_non_si_legge_da_la_cartolina_senza_logo(logo):
    """R-40: la cartolina esce con il solo nome, senza errori."""
    assert disegna_cartolina(NOME, TEMA, logo) == disegna_cartolina(NOME, TEMA)


@pytest.mark.parametrize("formato", ["PNG", "JPEG", "WEBP"])
def test_il_logo_si_legge_in_ogni_formato_del_profilo(formato):
    immagine = _apri(disegna_cartolina(NOME, TEMA, _logo(formato))).convert("RGB")

    rosso, verde, blu = immagine.getpixel((540, 754))
    # JPEG e WEBP non conservano la tinta esatta
    assert abs(rosso - ROSSO[0]) < 12 and verde < 60 and blu < 60


@pytest.mark.parametrize(
    ("misura", "attesa"),
    [
        ((300, 300), (160, 160)),  # quadrato: lo ferma l'altezza
        ((1200, 300), (320, 80)),  # largo: lo ferma la larghezza
        ((300, 1500), (32, 160)),  # stretto e alto
    ],
)
def test_il_logo_resta_nel_suo_riquadro_senza_deformarsi(misura, attesa):
    immagine = _apri(disegna_cartolina(NOME, TEMA, _logo(misura=misura)))
    larga, alta = attesa
    sinistra, basso = 540 - larga // 2, RIQUADRO_DEL_LOGO[3]

    rossi = [
        (x, y)
        for x in range(150, 930)
        for y in range(600, 862)
        if immagine.getpixel((x, y)) == ROSSO
    ]
    assert min(rossi) == (sinistra, basso - alta)
    assert max(rossi) == (sinistra + larga - 1, basso - 1)
    assert len(rossi) == larga * alta


def test_un_logo_con_lo_sfondo_trasparente_lascia_vedere_la_cartolina():
    trasparente = Image.new("RGBA", (600, 300), (0, 0, 0, 0))
    trasparente.paste(ROSSO + (255,), (150, 75, 450, 225))
    file = BytesIO()
    trasparente.save(file, format="PNG")

    immagine = _apri(disegna_cartolina(NOME, TEMA, file.getvalue())).convert("RGB")

    assert immagine.getpixel((540, 754)) == ROSSO
    assert immagine.getpixel((390, 684)) == SFONDO  # un angolo trasparente


@pytest.mark.parametrize(
    "tema",
    ["parola " * 200, "Supercalifragilistichespiralidoso" * 6, TEMA, "Sì"],
)
def test_il_tema_non_copre_il_logo(tema):
    """Un tema lungo si stringe nello spazio sopra il logo, dentro i margini."""
    immagine = _apri(disegna_cartolina(NOME, tema, _logo()))
    sinistra, alto, destra, basso = RIQUADRO_DEL_LOGO

    assert _colori_diversi_dallo_sfondo(immagine, (150, 108, 930, 634)) > 0
    assert _colori_diversi_dallo_sfondo(immagine, (60, 634, 1020, alto)) == 0
    assert _colori_diversi_dallo_sfondo(immagine, (60, alto, sinistra, basso)) == 0
    assert _colori_diversi_dallo_sfondo(immagine, (destra, alto, 1020, basso)) == 0
    assert _colori_diversi_dallo_sfondo(immagine, (0, 0, 1080, 50)) == 0


@pytest.mark.parametrize(
    ("nome", "tema"), [(NOME, None), (None, TEMA), (None, None), ("", "")]
)
def test_il_logo_c_e_anche_senza_tema_o_senza_nome(nome, tema):
    immagine = _apri(disegna_cartolina(nome, tema, _logo()))

    assert immagine.size == (1080, 1080)
    # con il tema il logo sta in basso, senza sta sopra il centro
    centro_del_logo = (540, 754) if tema else (540, 432)
    assert immagine.convert("RGB").getpixel(centro_del_logo) == ROSSO


# --- La foto ------------------------------------------------------------------


def test_ca77_il_logo_della_cartolina_e_quello_dello_snapshot(db, archivio):
    """Sostituito dopo l'invio, il logo nuovo non entra (R-40, costituzione §1.4)."""
    all_invio, dopo = _logo(), _logo(colore=BLU)
    bottega = profilo(db, nome=NOME, logo=archivio.salva(all_invio, "png"))
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    assert campagna.profilo_snapshot["logo"] == bottega.logo
    bottega.logo = archivio.salva(dopo, "png")
    db.flush()

    foto = componi_cartolina(db, campagna, TEMA)

    assert archivio.leggi(foto.file) == disegna_cartolina(NOME, TEMA, all_invio)
    assert archivio.leggi(foto.file) != disegna_cartolina(NOME, TEMA, dopo)
    assert archivio.leggi(foto.file) != disegna_cartolina(NOME, TEMA)


def test_ca77_logo_tolto_dopo_l_invio_la_cartolina_lo_porta_ancora(db, archivio):
    all_invio = _logo()
    bottega = profilo(db, nome=NOME, logo=archivio.salva(all_invio, "png"))
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    bottega.logo = None
    db.flush()

    foto = componi_cartolina(db, campagna, TEMA)

    assert archivio.leggi(foto.file) == disegna_cartolina(NOME, TEMA, all_invio)


def test_logo_messo_dopo_l_invio_non_entra_nella_cartolina(db, archivio):
    bottega = profilo(db, nome=NOME)
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    bottega.logo = archivio.salva(_logo(), "png")
    db.flush()

    foto = componi_cartolina(db, campagna, TEMA)

    assert archivio.leggi(foto.file) == disegna_cartolina(NOME, TEMA)


@pytest.mark.parametrize("logo", ["mai-salvato.png", "../fuori.png", 7])
def test_logo_che_non_si_trova_non_ferma_la_cartolina(db, archivio, logo):
    """Il file manca o il nome non è valido: cartolina con il solo nome."""
    campagna = campagna_inviata(db)
    campagna.profilo_snapshot = campagna.profilo_snapshot | {
        "nome": NOME,
        "logo": logo,
    }

    foto = componi_cartolina(db, campagna, TEMA)

    assert archivio.leggi(foto.file) == disegna_cartolina(NOME, TEMA)
    assert archivio.file_salvati == [foto.file]


def test_logo_che_non_e_un_immagine_non_ferma_la_cartolina(db, archivio):
    """Il file c'è ma non si apre più: cartolina con il solo nome."""
    bottega = profilo(db, nome=NOME, logo=archivio.salva(_logo(), "png"))
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    archivio._archivio[bottega.logo] = b"file rovinato"

    foto = componi_cartolina(db, campagna, TEMA)

    assert archivio.leggi(foto.file) == disegna_cartolina(NOME, TEMA)


def test_foto_creata_senza_gruppo_e_con_origine_cartolina(db, archivio):
    campagna = campagna_inviata(db)
    prima = len(campagne.foto_della_campagna(db, campagna.id))

    foto = componi_cartolina(db, campagna, TEMA)

    assert foto.id is not None
    assert foto.origine == "cartolina"
    assert foto.gruppo_id is None
    assert foto.campagna_id == campagna.id
    assert foto.profilo_id == campagna.profilo_id
    assert (foto.mime, foto.larghezza, foto.altezza) == ("image/png", 1080, 1080)
    assert foto.da_usare is False
    assert len(campagne.foto_della_campagna(db, campagna.id)) == prima + 1
    # la cartolina non entra in nessun gruppo della campagna
    gruppi = campagne.gruppi_della_campagna(db, campagna.id)
    assert foto.id not in {f.id for g in gruppi for f in g.foto}


def test_il_file_della_foto_e_nell_archivio_con_un_nome_del_server(db, archivio):
    campagna = campagna_inviata(db)

    foto = componi_cartolina(db, campagna, TEMA)

    assert archivio.file_salvati == [foto.file]
    assert foto.file.endswith(".png")
    assert TEMA not in foto.file
    immagine = _apri(archivio.leggi(foto.file))
    assert (immagine.format, immagine.size) == ("PNG", (1080, 1080))


def test_il_nome_della_bottega_viene_dallo_snapshot(db, archivio):
    """Costituzione §1.4: la fotografia del profilo, mai il profilo corrente."""
    bottega = profilo(db, nome="Nome all'invio")
    campagna = campagna_inviata(db, profilo_id=bottega.id)
    assert campagna.profilo_snapshot["nome"] == "Nome all'invio"
    bottega.nome = "Nome cambiato dopo"
    db.flush()

    foto = componi_cartolina(db, campagna, TEMA)

    assert archivio.leggi(foto.file) == disegna_cartolina("Nome all'invio", TEMA)
    assert archivio.leggi(foto.file) != disegna_cartolina("Nome cambiato dopo", TEMA)


def test_senza_snapshot_la_cartolina_esce_con_il_solo_tema(db, archivio):
    campagna = campagna_inviata(db, profilo_snapshot=None)

    foto = componi_cartolina(db, campagna, TEMA)

    assert archivio.leggi(foto.file) == disegna_cartolina(None, TEMA)


def test_ogni_cartolina_ha_il_suo_file(db, archivio):
    campagna = campagna_inviata(db)

    prima = componi_cartolina(db, campagna, TEMA)
    seconda = componi_cartolina(db, campagna, TEMA)

    assert prima.id != seconda.id
    assert prima.file != seconda.file
    assert sorted(archivio.file_salvati) == sorted([prima.file, seconda.file])


def test_nessun_file_fuori_dall_archivio_di_prova(db, tmp_path, monkeypatch):
    """Con l'archivio su disco il file nasce solo nella sua cartella."""
    radice = tmp_path / "archivio"
    altrove = tmp_path / "altrove"
    radice.mkdir()
    altrove.mkdir()
    monkeypatch.chdir(altrove)
    campagna = campagna_inviata(db)

    with usa_archivio(ArchivioDisco(radice=radice)):
        foto = componi_cartolina(db, campagna, TEMA)

    assert [p.name for p in radice.iterdir()] == [foto.file]
    assert list(altrove.iterdir()) == []
    assert sorted(p.name for p in tmp_path.iterdir()) == ["altrove", "archivio"]


def test_se_la_foto_non_si_crea_il_file_non_resta(db, archivio, monkeypatch):
    campagna = campagna_inviata(db)

    def fallisce(*args, **kwargs):
        raise RuntimeError("database non raggiungibile")

    monkeypatch.setattr(cartoline.campagne, "aggiungi_foto", fallisce)

    with pytest.raises(RuntimeError):
        componi_cartolina(db, campagna, TEMA)

    assert archivio.file_salvati == []
