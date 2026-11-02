"""Test per la sistemazione delle foto e criterio di accettazione CA-81.

Verifiche previste:
- CA-81: foto ruotata nei metadati, con GPS, PNG 3000 × 2000 -> sistemazione per Instagram ->
  JPEG dritta, senza GPS, 4:5 o 1:1 con lato corto 1080 px; l'originale resta intatto.
- Foto già conforme alle proporzioni (1:1 o 4:5): nessun ritaglio al centro.
- Foto fuori proporzioni: ritaglio al centro ottimale.
- Trattamento trasparenze e canali alpha (RGBA, WEBP).
- Rimozione completa dei metadati GPS.
- Autocontrasto e ridimensionamento a 1080 px.
- Integrazione con foto_sistemata() e database/archivio: l'originale resta intatto.
- Validazione errori e parametri non validi.
"""

from __future__ import annotations

import io
from PIL import Image, ImageDraw

import pytest

from app.adapters.archivio import ottieni_archivio
from app.core.errori import DatiNonValidi, NonTrovato
from app.moduli.campagne import service
from app.moduli.campagne.models import Foto
from app.moduli.campagne.sistemazione_foto import LATO_CORTO_TARGET


def _crea_immagine_png_con_exif_e_gps(
    larghezza: int = 3000,
    altezza: int = 2000,
    orientamento: int = 6,  # 6 = ruotata di 90 gradi in senso orario
) -> bytes:
    """Crea in memoria un PNG con metadati EXIF (Orientamento e blocco GPS)."""
    img = Image.new("RGB", (larghezza, altezza), color=(180, 100, 50))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 500, 500], fill=(240, 220, 150))

    # Prepara metadati EXIF
    exif = img.getexif()
    # 274 (0x0112) = Orientation
    exif[274] = orientamento

    # 34853 (0x8825) = GPSInfo IFD
    # Creiamo un IFD GPS con tag tipici (GPSVersionID, GPSLatitudeRef, GPSLatitude)
    gps_ifd = exif.get_ifd(34853)
    gps_ifd[0] = b"\x02\x03\x00\x00"  # Versione GPS
    gps_ifd[1] = "N"
    gps_ifd[2] = (45.0, 28.0, 15.0)
    gps_ifd[3] = "E"
    gps_ifd[4] = (9.0, 12.0, 30.0)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG", exif=exif)
    return buffer.getvalue()


class TestSistemazioneFotoCA81:
    """Test dedicato al criterio di accettazione CA-81 e invarianti R-42."""

    def test_ca81_sistemazione_instagram(self):
        """CA-81: foto ruotata nei metadati, con GPS, PNG 3000 x 2000 -> sistemazione per Instagram ->

        JPEG dritta, senza GPS, 4:5 o 1:1 con lato corto 1080 px; l'originale resta.
        """
        png_originale = _crea_immagine_png_con_exif_e_gps(3000, 2000, orientamento=6)
        copia_per_controllo = bytes(png_originale)

        # Esegue la sistemazione per il canale Instagram
        jpeg_risultato = service.sistema_foto(png_originale, canale="instagram")

        # 1. Verifica formato JPEG valido
        assert (
            jpeg_risultato[:2] == b"\xff\xd8"
        ), "L'output deve essere un file JPEG valido."

        # 2. Verifica che il buffer originale non sia stato mutato
        assert (
            png_originale == copia_per_controllo
        ), "L'immagine originale non deve essere alterata."

        # 3. Analisi dell'immagine risultante
        img_risultato = Image.open(io.BytesIO(jpeg_risultato))
        assert img_risultato.format == "JPEG"

        # 4. Verifica dimensioni e lato corto 1080 px
        w, h = img_risultato.width, img_risultato.height
        lato_corto = min(w, h)
        assert (
            lato_corto == LATO_CORTO_TARGET
        ), f"Il lato corto deve essere 1080 px, trovato {lato_corto} px."

        # 5. Verifica proporzioni (4:5 o 1:1)
        ratio = w / h
        is_uno_a_uno = abs(ratio - 1.0) <= 0.02
        is_quattro_a_cinque = abs(ratio - (4 / 5)) <= 0.02
        assert (
            is_uno_a_uno or is_quattro_a_cinque
        ), f"Le proporzioni risultanti ({w}x{h}, ratio={ratio:.3f}) devono essere 1:1 o 4:5."

        # 6. Verifica che non contenga dati GPS
        exif_out = img_risultato.getexif()
        # Il tag 34853 (GPSInfo) non deve esistere
        assert (
            34853 not in exif_out
        ), "I metadati GPS devono essere stati completamente rimossi."
        gps_ifd = exif_out.get_ifd(34853)
        assert len(gps_ifd) == 0, "Il blocco GPS IFD deve essere vuoto o assente."

    def test_ca81_forzatura_proporzione_quattro_quinti(self):
        """Verifica che specificando la proporzione 4:5 l'output sia esattamente 1080x1350."""
        png_originale = _crea_immagine_png_con_exif_e_gps(3000, 2000, orientamento=1)

        jpeg_risultato = service.sistema_foto(
            png_originale, canale="instagram", proporzione="4:5"
        )
        img = Image.open(io.BytesIO(jpeg_risultato))
        assert img.width == 1080
        assert img.height == 1350
        assert min(img.width, img.height) == 1080

    def test_ca81_forzatura_proporzione_uno_a_uno(self):
        """Verifica che specificando la proporzione 1:1 l'output sia esattamente 1080x1080."""
        png_originale = _crea_immagine_png_con_exif_e_gps(3000, 2000, orientamento=1)

        jpeg_risultato = service.sistema_foto(
            png_originale, canale="instagram", proporzione="1:1"
        )
        img = Image.open(io.BytesIO(jpeg_risultato))
        assert img.width == 1080
        assert img.height == 1080
        assert min(img.width, img.height) == 1080


class TestProporzioniVereCA81:
    """CA-81 rivisto: l'intervallo da 4:5 a 1,91:1 non si taglia."""

    @staticmethod
    def _jpeg(larghezza: int, altezza: int) -> bytes:
        buf = io.BytesIO()
        Image.new("RGB", (larghezza, altezza), (90, 140, 60)).save(buf, "JPEG")
        return buf.getvalue()

    def test_ca81_tre_a_due_resta_tre_a_due_senza_taglio(self):
        png = _crea_immagine_png_con_exif_e_gps(3000, 2000, orientamento=1)
        out = Image.open(io.BytesIO(service.sistema_foto(png, canale="instagram")))
        assert out.size == (1620, 1080)

    def test_ca81_verticale_stretta_va_a_quattro_quinti(self):
        out = Image.open(
            io.BytesIO(service.sistema_foto(self._jpeg(1080, 1920), canale="instagram"))
        )
        assert out.size == (1080, 1350)

    def test_ca81_panoramica_va_a_uno_virgola_91(self):
        out = Image.open(
            io.BytesIO(service.sistema_foto(self._jpeg(4000, 1000), canale="facebook"))
        )
        assert out.height == 1080
        assert abs(out.width / out.height - 1.91) < 0.01

    @pytest.mark.parametrize("canale", ["facebook", "instagram"])
    @pytest.mark.parametrize(
        ("larghezza", "altezza", "atteso"),
        [
            (1910, 1000, (2063, 1080)),
            (1600, 2000, (1080, 1350)),
            (1500, 1000, (1620, 1080)),
        ],
    )
    def test_ca81_gli_estremi_e_il_dentro_non_si_tagliano(
        self, canale, larghezza, altezza, atteso
    ):
        dati = self._jpeg(larghezza, altezza)
        out = Image.open(io.BytesIO(service.sistema_foto(dati, canale=canale)))
        assert abs(out.width - atteso[0]) <= 1 and out.height == atteso[1]


class TestSistemazioneFotoRegole:
    """Test delle regole di business R-21 e R-42."""

    def test_foto_gia_in_proporzione_uno_a_uno_non_ritaglia(self):
        """Una foto quadrata (es. 2000x2000) non subisce ritaglio, solo resize a 1080x1080."""
        img = Image.new("RGB", (2000, 2000), color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        dati_in = buf.getvalue()

        dati_out = service.sistema_foto(dati_in, canale="facebook")
        img_out = Image.open(io.BytesIO(dati_out))
        assert img_out.width == 1080
        assert img_out.height == 1080

    def test_foto_gia_in_proporzione_quattro_quinti_non_ritaglia(self):
        """Una foto 4:5 (es. 1600x2000) non subisce ritaglio, solo resize a 1080x1350."""
        img = Image.new("RGB", (1600, 2000), color=(120, 180, 210))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        dati_in = buf.getvalue()

        dati_out = service.sistema_foto(dati_in, canale="instagram")
        img_out = Image.open(io.BytesIO(dati_out))
        assert img_out.width == 1080
        assert img_out.height == 1350

    def test_foto_con_trasparenza_rgba(self):
        """Un'immagine RGBA con canale alfa viene salvata come JPEG con sfondo pulito."""
        img = Image.new("RGBA", (1500, 1500), color=(200, 50, 50, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        dati_in = buf.getvalue()

        dati_out = service.sistema_foto(dati_in, canale="facebook")
        img_out = Image.open(io.BytesIO(dati_out))
        assert img_out.format == "JPEG"
        assert img_out.mode == "RGB"
        assert img_out.width == 1080
        assert img_out.height == 1080

    def test_foto_cmyk_convertita_in_rgb(self):
        """Un'immagine in formato CMYK viene convertita correttamente a RGB."""
        img = Image.new("CMYK", (1500, 1500), color=(0, 128, 128, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        dati_out = service.sistema_foto(buf.getvalue(), canale="instagram")
        img_out = Image.open(io.BytesIO(dati_out))
        assert img_out.format == "JPEG"
        assert img_out.mode == "RGB"
        assert img_out.size == (1080, 1080)

    def test_foto_in_scala_di_grigi_e_monocromatica(self):
        """Immagini in scala di grigi (L) e 1-bit vengono convertite a RGB senza errori."""
        for modo in ("L", "1"):
            img = Image.new(modo, (1200, 1500), color=1)
            buf = io.BytesIO()
            img.save(buf, format="PNG")

            dati_out = service.sistema_foto(buf.getvalue(), canale="facebook")
            img_out = Image.open(io.BytesIO(dati_out))
            assert img_out.format == "JPEG"
            assert img_out.mode == "RGB"
            assert img_out.size == (1080, 1350)

    def test_foto_troppo_grande_anti_dos_solleva_errore(self, monkeypatch):
        """Immagini con dimensioni sproporzionate (> 36 MP) vengono bloccate preventivamente (Anti-DoS)."""
        import app.moduli.campagne.sistemazione_foto as modulo_sist

        # Simuliamo un limite basso per testare la guardia difensiva
        monkeypatch.setattr(modulo_sist, "MAX_PIXEL_TOTALI", 100_000)

        img = Image.new("RGB", (500, 500))  # 250.000 pixel > 100.000
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        with pytest.raises(DatiNonValidi, match="troppo grande"):
            service.sistema_foto(buf.getvalue(), canale="instagram")

    def test_ritaglio_centrato_simmetrico(self):
        """Verifica che il ritaglio sia centrato simmetricamente rispetto all'originale."""
        # Creiamo un'immagine 3000x2000 con un punto centrale identificabile
        img = Image.new("RGB", (3000, 2000), color=(0, 0, 0))
        # Disegniamo un quadrato bianco al centro esatto (x da 1400 a 1600, y da 900 a 1100)
        draw = ImageDraw.Draw(img)
        draw.rectangle([1400, 900, 1600, 1100], fill=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        dati_out = service.sistema_foto(
            buf.getvalue(), canale="instagram", proporzione="1:1"
        )
        img_out = Image.open(io.BytesIO(dati_out))
        assert img_out.size == (1080, 1080)
        # Il pixel centrale deve essere bianco (255, 255, 255)
        pixel_centro = img_out.getpixel((540, 540))
        assert pixel_centro == (
            255,
            255,
            255,
        ), "Il soggetto al centro deve rimanere esattamente al centro."

    def test_concorrenza_e_thread_safety(self):
        """Verifica che chiamate concorrenti parallele su thread diversi siano completamente isolate."""
        import concurrent.futures

        img1 = Image.new("RGB", (2000, 2000), color=(255, 0, 0))
        buf1 = io.BytesIO()
        img1.save(buf1, format="JPEG")
        dati1 = buf1.getvalue()

        img2 = Image.new("RGB", (1600, 2000), color=(0, 255, 0))
        buf2 = io.BytesIO()
        img2.save(buf2, format="JPEG")
        dati2 = buf2.getvalue()

        def _elabora(dati, canale):
            return service.sistema_foto(dati, canale=canale)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            f1 = [executor.submit(_elabora, dati1, "instagram") for _ in range(5)]
            f2 = [executor.submit(_elabora, dati2, "facebook") for _ in range(5)]
            risultati1 = [f.result() for f in f1]
            risultati2 = [f.result() for f in f2]

        for r in risultati1:
            im = Image.open(io.BytesIO(r))
            assert im.size == (1080, 1080)
        for r in risultati2:
            im = Image.open(io.BytesIO(r))
            assert im.size == (1080, 1350)

    def test_canale_non_valido_solleva_errore(self):
        img = Image.new("RGB", (1080, 1080), color=(50, 50, 50))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        with pytest.raises(DatiNonValidi, match="non valido"):
            service.sistema_foto(buf.getvalue(), canale="canale_inesistente")

    def test_proporzione_non_valida_solleva_errore(self):
        img = Image.new("RGB", (1080, 1080), color=(50, 50, 50))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        with pytest.raises(DatiNonValidi, match="Proporzione"):
            service.sistema_foto(buf.getvalue(), canale="instagram", proporzione="16:9")

    def test_dati_vuoti_o_corrotti_sollevano_errore(self):
        with pytest.raises(DatiNonValidi, match="Nessun dato"):
            service.sistema_foto(b"", canale="instagram")

        with pytest.raises(DatiNonValidi, match="corrotto"):
            service.sistema_foto(b"dati casuali non immagine", canale="instagram")


class TestFotoSistemataDatabase:
    """Test della funzione foto_sistemata() con database e archivio (Costituzione §1.3)."""

    def test_foto_sistemata_legge_da_archivio_e_non_altera_originale(self, db):
        """Verifica che foto_sistemata() ritorni i byte JPEG senza alterare il file su disco."""
        from tests.moduli.artigiani.fabbrica import profilo

        bottega = profilo(db)

        # 1. Creiamo un file originale PNG nell'archivio
        archivio = ottieni_archivio()
        dati_originali = _crea_immagine_png_con_exif_e_gps(2000, 1500, orientamento=1)
        nome_file = archivio.salva(dati_originali, ".png")

        # 2. Creiamo il record Foto nel DB
        foto = Foto(
            profilo_id=bottega.id,
            file=nome_file,
            mime="image/png",
            larghezza=2000,
            altezza=1500,
            origine="caricata",
            da_usare=False,
            pubblicata_su={},
        )
        db.add(foto)
        db.flush()

        # 3. Chiamata a foto_sistemata
        jpeg_bytes, mime = service.foto_sistemata(
            db=db, foto_id=foto.id, canale="instagram"
        )

        assert mime == "image/jpeg"
        assert jpeg_bytes[:2] == b"\xff\xd8"

        img = Image.open(io.BytesIO(jpeg_bytes))
        assert min(img.width, img.height) == 1080

        # 4. Invariante fondamentale: il file originale su disco non è modificato!
        file_su_disco = archivio.leggi(nome_file)
        assert (
            file_su_disco == dati_originali
        ), "Il file originale archiviato deve rimanere intatto al 100%."

    def test_foto_sistemata_non_trovata_solleva_404(self, db):
        with pytest.raises(NonTrovato, match="Foto non trovata"):
            service.foto_sistemata(db=db, foto_id=999999, canale="instagram")


class TestSistemazioneFotoCA114:
    """Test del criterio di accettazione CA-114 (ADR-119, brief §1.5).

    Regole:
    - foto 6000 x 2000 con il soggetto a sinistra -> 1,91:1 con il riquadro intero;
    - foto 1080 x 2400 con il riquadro che non entra in 4:5 -> bordi sfocati, foto intera;
    - senza riquadro e un taglio oltre il 10% -> bordi sfocati;
    - senza riquadro e un taglio entro il 10% -> ritaglio al centro;
    - mai deformata; l'originale non cambia.
    """

    @staticmethod
    def _crea_foto(
        larghezza: int, altezza: int, colore: tuple[int, int, int] = (100, 150, 200)
    ) -> Image.Image:
        return Image.new("RGB", (larghezza, altezza), color=colore)

    @staticmethod
    def _to_jpeg(img: Image.Image) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue()

    def test_ca114_ritaglio_soggetto_a_sinistra_panoramica(self):
        """foto 6000 x 2000 con il soggetto a sinistra -> 1,91:1 con il riquadro intero."""
        # Creiamo foto 6000x2000 nera con un quadrato bianco a sinistra (il soggetto)
        img = self._crea_foto(6000, 2000, (0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Soggetto a sinistra: x da 300 a 1500 (5% a 25%), y da 400 a 1600 (20% a 80%)
        # normalizzato: x=0.05, y=0.20, larghezza=0.20, altezza=0.60
        draw.rectangle([300, 400, 1500, 1600], fill=(255, 255, 255))
        soggetto_box = {
            "x": 0.05,
            "y": 0.20,
            "larghezza": 0.20,
            "altezza": 0.60,
        }

        dati_in = self._to_jpeg(img)
        dati_out = service.sistema_foto(
            dati_in, canale="facebook", soggetto_box=soggetto_box
        )
        img_out = Image.open(io.BytesIO(dati_out))

        # Deve avere proporzione 1.91:1 con altezza 1080 px
        assert img_out.height == 1080
        ratio = img_out.width / img_out.height
        assert abs(ratio - 1.91) < 0.02

        # Poiché il soggetto era a sinistra e il riquadro è intero:
        # La finestra 1.91 (larghezza 3820 su 6000) centrata sul soggetto parte da x=0
        # Nel risultato finale (larghezza 2063 px), il soggetto (era a x=300..1500 su 3820)
        # deve essere visibile verso sinistra (pixel bianco)
        # Controlliamo che il pixel del soggetto sia effettivamente bianco
        # x_norm nel crop: (300 + 1500)/2 / 3820 = 900 / 3820 ~= 0.235
        # su 2063 px: ~485 px
        pixel_soggetto = img_out.getpixel(
            (round(img_out.width * 0.235), round(img_out.height * 0.5))
        )
        assert (
            pixel_soggetto[0] > 200 and pixel_soggetto[1] > 200
        ), "Il soggetto a sinistra deve essere contenuto interamente nell'immagine ritagliata."

        # Se fosse stato un ritaglio al centro (senza riquadro), il crop x partirebbe da (6000 - 3820)/2 = 1090
        # e perderebbe la parte sinistra del soggetto da x=300 a x=1090 (il riquadro non sarebbe intero)

    def test_ca114_riquadro_che_non_entra_bordi_sfocati(self):
        """foto 1080 x 2400 con il riquadro che non entra in 4:5 -> bordi sfocati, foto intera."""
        # Se la foto è 1080x2400 (rapporto 0.45) e il target è 4:5 (0.8),
        # un ritaglio a 4:5 richiederebbe altezza 1080 / 0.8 = 1350 px.
        # Se il riquadro del soggetto ha altezza 1800 px (0.75 dell'altezza totale),
        # non può entrare nella finestra di 1350 px -> deve applicare bordi sfocati!
        img = self._crea_foto(1080, 2400, (50, 120, 80))
        soggetto_box = {
            "x": 0.1,
            "y": 0.1,
            "larghezza": 0.8,
            "altezza": 0.75,  # 0.75 * 2400 = 1800 px > 1350 px finestra ritaglio
        }

        dati_in = self._to_jpeg(img)
        dati_out = service.sistema_foto(
            dati_in, canale="instagram", soggetto_box=soggetto_box
        )
        img_out = Image.open(io.BytesIO(dati_out))

        # Output in proporzione 4:5 (1080x1350)
        assert img_out.size == (1080, 1350)

    def test_ca114_senza_riquadro_taglio_oltre_dieci_percento_bordi_sfocati(self):
        """senza riquadro e un taglio oltre il 10% -> bordi sfocati; mai deformata."""
        # Foto 1080 x 2000 (rapporto 0.54)
        # Portarla a 4:5 (0.8) con ritaglio taglierebbe l'altezza da 2000 a 1350 px,
        # togliendo (2000 - 1350) / 2000 = 32.5% dell'area (> 10%).
        # Senza riquadro, deve andare a bordi sfocati.
        img = self._crea_foto(1080, 2000, (60, 90, 140))
        draw = ImageDraw.Draw(img)
        # Disegniamo punti identificativi agli estremi in alto e in basso
        draw.rectangle([500, 20, 580, 100], fill=(255, 0, 0))
        draw.rectangle([500, 1900, 580, 1980], fill=(0, 255, 0))

        dati_in = self._to_jpeg(img)
        dati_out = service.sistema_foto(dati_in, canale="instagram", soggetto_box=None)
        img_out = Image.open(io.BytesIO(dati_out))

        assert img_out.size == (1080, 1350)
        # Con i bordi sfocati la foto originale è intera verticalmente (nessun taglio sopra/sotto):
        # i punti in alto e in basso devono essere preservati (visibili lungo l'asse centrale)
        pixel_alto = img_out.getpixel((540, round(1350 * (60 / 2000))))
        pixel_basso = img_out.getpixel((540, round(1350 * (1940 / 2000))))
        # Il punto rosso in alto ha forte componente R
        assert pixel_alto[0] > 150
        # Il punto verde in basso ha forte componente G
        assert pixel_basso[1] > 150

    def test_ca114_senza_riquadro_taglio_entro_dieci_percento_ritaglio_centro(self):
        """senza riquadro e un taglio entro il 10% -> ritaglio al centro."""
        # Foto 2000 x 1100 (rapporto ~1.818): dentro l'intervallo [0.8, 1.91], non si taglia.
        # Foto 2000 x 1000 (rapporto 2.0 > 1.91).
        # Per andare a 1.91:1 (w_crop = 1910, h_crop = 1000).
        # Taglio: (2000 - 1910) / 2000 = 90 / 2000 = 4.5% (<= 10%).
        # Deve eseguire ritaglio al centro!
        img = self._crea_foto(2000, 1000, (0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Disegniamo un cerchio/quadrato bianco al centro esatto
        draw.rectangle([950, 450, 1050, 550], fill=(255, 255, 255))
        # Disegniamo strisce rosse ai bordi estremi sinistro e destro che devono essere tagliate
        draw.rectangle([0, 0, 30, 1000], fill=(255, 0, 0))
        draw.rectangle([1970, 0, 2000, 1000], fill=(255, 0, 0))

        dati_in = self._to_jpeg(img)
        dati_out = service.sistema_foto(dati_in, canale="facebook", soggetto_box=None)
        img_out = Image.open(io.BytesIO(dati_out))

        assert img_out.height == 1080
        assert abs(img_out.width / img_out.height - 1.91) < 0.02
        # Il centro deve essere intatto
        pixel_centro = img_out.getpixel((img_out.width // 2, img_out.height // 2))
        assert pixel_centro[0] > 200 and pixel_centro[1] > 200

    def test_ca114_foto_sistemata_usa_soggetto_box_da_analisi_ai(self, db):
        """foto_sistemata() legge foto.analisi_ai['soggetto_box'] e lo usa per il ritaglio."""
        from tests.moduli.artigiani.fabbrica import profilo

        bottega = profilo(db)
        archivio = ottieni_archivio()

        # Foto 6000x2000 con soggetto a destra
        img = self._crea_foto(6000, 2000, (0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Soggetto a destra: x da 4500 a 5700 (0.75 a 0.95), y da 400 a 1600 (0.2 a 0.8)
        draw.rectangle([4500, 400, 5700, 1600], fill=(255, 255, 255))
        soggetto_box = {
            "x": 0.75,
            "y": 0.20,
            "larghezza": 0.20,
            "altezza": 0.60,
        }

        dati_orig = self._to_jpeg(img)
        nome_file = archivio.salva(dati_orig, ".jpg")

        foto = Foto(
            profilo_id=bottega.id,
            file=nome_file,
            mime="image/jpeg",
            larghezza=6000,
            altezza=2000,
            origine="caricata",
            da_usare=False,
            pubblicata_su={},
            analisi_ai={"soggetto_box": soggetto_box},
        )
        db.add(foto)
        db.flush()

        jpeg_bytes, mime = service.foto_sistemata(
            db=db, foto_id=foto.id, canale="facebook"
        )
        assert mime == "image/jpeg"
        out = Image.open(io.BytesIO(jpeg_bytes))
        assert out.height == 1080
        # Poiché il soggetto era a destra, il ritaglio si è spostato a destra (crop da 2180 a 6000)
        # Nel risultato finale (2063 px), verso destra il soggetto è bianco
        pixel_dx = out.getpixel((round(out.width * 0.8), round(out.height * 0.5)))
        assert pixel_dx[0] > 200 and pixel_dx[1] > 200
