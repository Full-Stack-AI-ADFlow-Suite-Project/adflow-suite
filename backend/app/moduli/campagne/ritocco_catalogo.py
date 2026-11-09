"""Il catalogo del ritocco: codici, fasce, parametri e versioni in un posto solo (ADR-124, RT-12).

Quello che l'AI può dire di una foto (le ``note`` e i ruoli delle zone), le fasce
in cui si dividono le misure, i parametri delle varianti Standard e Spinta e le
versioni dei pezzi stanno qui e solo qui. Lo schema dell'AI (``adapters/ai/schemi.py``)
ne tiene copie, che un test confronta con questo file: l'adapter non importa i
moduli (plan §5).

I valori numerici sono di partenza e prudenti: si tarano sulle foto reali con
``prova-ritocco`` (RT-34). Cambiarli cambia l'uscita delle foto: se cambia ciò che
l'esecutore produce, si alza ``VERSIONE_RITOCCO`` (entra nella chiave dei render).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# --- Versioni ----------------------------------------------------------------------
# Dicono con quale versione del pezzo è stata salvata un'analisi: se cambiano, le foto
# già analizzate si ricalcolano senza AI (``ricalcola-ritocco``, RT-27).

VERSIONE_LOCALE: Final[str] = "locale-1"  # misure, fasce, candidati (L1)
VERSIONE_DIAGNOSI: Final[str] = "diagnosi-1"  # doppia chiave, zone, avvisi (L2)
VERSIONE_RITOCCO: Final[
    str
] = "ritocco-1"  # esecutore e varianti (L3): = VERSIONE_ESECUTORE

# --- Che cosa può fare un codice ---------------------------------------------------

# Gli effetti ammessi: ogni codice ne dichiara uno (nota 12.2). Con la doppia chiave
# (nota 10.7) un effetto di correzione scatta solo se anche la misura lo conferma.
EFFETTI: Final[frozenset[str]] = frozenset(
    {
        "avvicinamento",  # finestra più stretta sul soggetto
        "avvicinamento_limitato",  # come sopra, con un tetto più basso
        "nessun_avvicinamento",  # la finestra resta quella del rapporto
        "rotazione_fine",  # raddrizza dell'angolo misurato
        "ruota",  # rotazione di 90°, prima di tutto, anche in Originale
        "esposizione",
        "ombre",
        "flash",
        "bianco",  # solo con una zona ``neutro``
        "esclusione_bordi",
        "avviso",
        "solo_originale",  # nessuna correzione: screenshot e grafica
        "nessuno",  # informa il testo e l'operatore, non la foto
        "privacy",  # propone una zona da oscurare
        "finestra",  # protegge o sposta la finestra (``tieni``, ``togli``)
        "riferimento",  # superficie di riferimento (``neutro``)
    }
)


@dataclass(frozen=True)
class Codice:
    """Un codice che l'AI può scrivere: che cosa vuol dire e che cosa ne fa il codice."""

    significato: str
    effetto: str


# Nota: tutto ciò che l'AI può segnalare di una foto. Gli stessi nomi, nello stesso
# ordine, stanno in ``adapters/ai/schemi.py::Nota`` (RT-20).
NOTE: Final[dict[str, Codice]] = {
    # inquadratura
    "lontana": Codice("il soggetto è piccolo", "avvicinamento"),
    "decentrata": Codice("il soggetto è fuori centro", "avvicinamento"),
    "storta": Codice("orizzonte o verticali pendono senza motivo", "rotazione_fine"),
    "ambiente": Codice("la foto racconta un luogo", "avvicinamento_limitato"),
    "non_tagliare": Codice(
        "tagliare toglierebbe qualcosa di importante", "nessun_avvicinamento"
    ),
    "ruota_90": Codice("la foto è girata di 90°", "ruota"),
    "ruota_180": Codice("la foto è capovolta", "ruota"),
    "ruota_270": Codice("la foto è girata di 270°", "ruota"),
    # luce
    "scura": Codice("difetto di esposizione, non il buio voluto", "esposizione"),
    "chiara": Codice("troppo chiara, non il chiaro voluto", "esposizione"),
    "controluce": Codice("il soggetto è in ombra davanti a una luce forte", "ombre"),
    "flash": Codice("flash frontale: bordi più scuri del centro", "flash"),
    "calda": Codice("dominante calda sul soggetto", "bianco"),
    "fredda": Codice("dominante fredda sul soggetto", "bianco"),
    "verde": Codice("dominante verde sul soggetto", "bianco"),
    "magenta": Codice("dominante magenta sul soggetto", "bianco"),
    "riflessi_bordi": Codice(
        "riflessi di vetri, bottiglie o smalti ai bordi", "esclusione_bordi"
    ),
    "riflessi_soggetto": Codice("riflessi sul soggetto", "avviso"),
    # qualità e tipo
    "mossa_lieve": Codice("movimento non voluto, lieve", "avviso"),
    "mossa_forte": Codice("movimento non voluto, forte", "avviso"),
    "foto_di_foto": Codice("è la fotografia di una fotografia", "avviso"),
    "screenshot": Codice("è una schermata", "solo_originale"),
    "grafica": Codice("è una grafica, non una foto", "solo_originale"),
    # altro
    "marchi": Codice("loghi o marchi di altre aziende", "avviso"),
}

# RuoloZona: a che cosa serve un riquadro che l'AI segna nella foto.
RUOLI_ZONA: Final[dict[str, Codice]] = {
    "tieni": Codice("testo o elemento da non tagliare", "finestra"),
    "togli": Codice("intruso ai bordi", "finestra"),
    "neutro": Codice("superficie bianca o grigia di riferimento", "riferimento"),
    "volto": Codice("volto riconoscibile senza codice V", "privacy"),
    "nome": Codice("scritta con un nome di persona", "privacy"),
    "indirizzo": Codice("scritta con un indirizzo", "privacy"),
    "targa": Codice("targa di un veicolo", "privacy"),
    "dati": Codice("altri dati personali scritti", "privacy"),
}

# Le note che non ammettono altro che l'Originale e le coppie in conflitto (le due si
# scartano insieme: nota 12.2, validatori morbidi).
NOTE_SOLO_ORIGINALE: Final[frozenset[str]] = frozenset(
    codice for codice, c in NOTE.items() if c.effetto == "solo_originale"
)
NOTE_IN_CONFLITTO: Final[tuple[frozenset[str], ...]] = (
    frozenset({"scura", "chiara"}),
    frozenset({"mossa_lieve", "mossa_forte"}),
    frozenset({"calda", "fredda"}),
    frozenset({"verde", "magenta"}),
)
NOTE_DOMINANTE: Final[frozenset[str]] = frozenset(
    {"calda", "fredda", "verde", "magenta"}
)

# --- Le fasce delle misure ---------------------------------------------------------


@dataclass(frozen=True)
class Fascia:
    """Come una misura si traduce in parole per l'AI (nota 9.5).

    ``nomi`` va dal valore più basso al più alto; ``soglie`` sono i confini fra un
    nome e il successivo (uno in meno dei nomi, in ordine crescente, dentro
    ``dominio``): un valore *uguale* a una soglia sta nella fascia di sopra.
    ``normali`` sono le fasce che non si mandano all'AI.
    """

    misura: str
    unita: str
    dominio: tuple[float, float]
    nomi: tuple[str, ...]
    soglie: tuple[float, ...]
    normali: frozenset[str]

    def di(self, valore: float) -> str:
        """Il nome della fascia in cui cade ``valore``."""
        for nome, soglia in zip(self.nomi, self.soglie):
            if valore < soglia:
                return nome
        return self.nomi[-1]


FASCE: Final[dict[str, Fascia]] = {
    # Varianza del Laplaciano della luminanza, sulla copia di lavoro (lato lungo 2048).
    "nitidezza": Fascia(
        "nitidezza",
        "varianza",
        (0.0, 65025.0),
        ("bassa", "media", "alta"),
        (30.0, 150.0),
        frozenset({"media", "alta"}),
    ),
    # Luminanza mediana in L* (0 nero, 100 bianco).
    "esposizione": Fascia(
        "esposizione",
        "L*",
        (0.0, 100.0),
        ("scura", "normale", "chiara"),
        (30.0, 75.0),
        frozenset({"normale"}),
    ),
    # Quota di pixel con luminanza >= 250 su 255.
    "luci_bruciate": Fascia(
        "luci_bruciate",
        "%",
        (0.0, 100.0),
        ("nessuna", "poche", "molte"),
        (0.5, 3.0),
        frozenset({"nessuna"}),
    ),
    # Quota di pixel con luminanza <= 5 su 255.
    "ombre_chiuse": Fascia(
        "ombre_chiuse",
        "%",
        (0.0, 100.0),
        ("nessuna", "poche", "molte"),
        (1.0, 5.0),
        frozenset({"nessuna"}),
    ),
    # Qualità del JPEG stimata dalle tabelle di quantizzazione (1–100).
    "compressione": Fascia(
        "compressione",
        "qualità",
        (1.0, 100.0),
        ("forte", "lieve", "nessuna"),
        (70.0, 90.0),
        frozenset({"nessuna"}),
    ),
}

# La dominante non è una fascia sola: serve il modulo di (a*, b*) sulle zone neutre
# del soggetto e poi l'asse prevalente.
DOMINANTE_SOGLIA: Final[float] = 6.0  # sotto, "nessuna" (unità di a*/b*)
DOMINANTE_DOMINIO: Final[tuple[float, float]] = (0.0, 200.0)
DOMINANTE_ASSI: Final[dict[str, str]] = {
    "b+": "calda",
    "b-": "fredda",
    "a-": "verde",
    "a+": "magenta",
}

# --- Le varianti: Standard e Spinta ------------------------------------------------


@dataclass(frozen=True)
class Parametri:
    """Dosi e tetti di una variante (nota 12.5). Valori di partenza, da tarare (RT-34)."""

    # Inquadratura
    avvicinamento_senza_nota_sotto: float  # soggetto più piccolo di questa quota → avvicina
    margine_avvicinamento: float  # margine intorno al soggetto, in quota della finestra
    ingrandimento_max: float  # 1,0 = nessun ingrandimento
    intrusi_taglio_max: float  # quota d'area che si può tagliare per togliere un intruso
    ambiente_taglio_max: float  # quota d'area che si può tagliare con ``ambiente``
    # Geometria
    rotazione_max_gradi: float
    prospettiva_deformazione_max: float
    # Luce
    esposizione_tetto_stop: float
    esposizione_scarto_minimo_stop: float  # scarto misurato che conferma l'AI
    bianco_tetto_canale: float  # con una zona ``neutro``
    bianco_senza_neutro_tetto: float  # 0: mai senza ``neutro``
    ombre_dose: float
    flash_dose: float
    nitidezza_dose: float


STANDARD: Final[Parametri] = Parametri(
    avvicinamento_senza_nota_sotto=0.0,
    margine_avvicinamento=0.10,
    ingrandimento_max=1.0,
    intrusi_taglio_max=0.15,
    ambiente_taglio_max=0.10,
    rotazione_max_gradi=5.0,
    prospettiva_deformazione_max=0.08,
    esposizione_tetto_stop=0.5,
    esposizione_scarto_minimo_stop=0.3,
    bianco_tetto_canale=0.05,
    bianco_senza_neutro_tetto=0.0,
    ombre_dose=0.25,  # lieve
    flash_dose=0.0,  # spento
    nitidezza_dose=0.3,  # lieve
)

SPINTA: Final[Parametri] = Parametri(
    avvicinamento_senza_nota_sotto=0.40,
    margine_avvicinamento=0.05,
    ingrandimento_max=1.3,
    intrusi_taglio_max=0.30,
    ambiente_taglio_max=0.20,
    rotazione_max_gradi=8.0,
    prospettiva_deformazione_max=0.15,
    esposizione_tetto_stop=1.0,
    esposizione_scarto_minimo_stop=0.15,
    bianco_tetto_canale=0.10,
    bianco_senza_neutro_tetto=0.04,
    ombre_dose=0.5,  # media
    flash_dose=0.5,  # acceso
    nitidezza_dose=0.6,  # media
)

# Soglia sotto la quale una rotazione non vale la pena (zona morta): vale per tutte.
ROTAZIONE_MIN_GRADI: Final[float] = 0.5

# Il parametro è più forte quando è più grande ("maggiore") o più piccolo ("minore").
SENSO: Final[dict[str, str]] = {
    "avvicinamento_senza_nota_sotto": "maggiore",
    "margine_avvicinamento": "minore",
    "ingrandimento_max": "maggiore",
    "intrusi_taglio_max": "maggiore",
    "ambiente_taglio_max": "maggiore",
    "rotazione_max_gradi": "maggiore",
    "prospettiva_deformazione_max": "maggiore",
    "esposizione_tetto_stop": "maggiore",
    "esposizione_scarto_minimo_stop": "minore",
    "bianco_tetto_canale": "maggiore",
    "bianco_senza_neutro_tetto": "maggiore",
    "ombre_dose": "maggiore",
    "flash_dose": "maggiore",
    "nitidezza_dose": "maggiore",
}

# Il valore ammesso di ogni parametro (minimo, massimo), per i controlli di coerenza.
DOMINIO_PARAMETRI: Final[dict[str, tuple[float, float]]] = {
    "avvicinamento_senza_nota_sotto": (0.0, 1.0),
    "margine_avvicinamento": (0.0, 0.5),
    "ingrandimento_max": (1.0, 2.0),
    "intrusi_taglio_max": (0.0, 1.0),
    "ambiente_taglio_max": (0.0, 1.0),
    "rotazione_max_gradi": (ROTAZIONE_MIN_GRADI, 45.0),
    "prospettiva_deformazione_max": (0.0, 1.0),
    "esposizione_tetto_stop": (0.0, 3.0),
    "esposizione_scarto_minimo_stop": (0.0, 3.0),
    "bianco_tetto_canale": (0.0, 0.5),
    "bianco_senza_neutro_tetto": (0.0, 0.5),
    "ombre_dose": (0.0, 1.0),
    "flash_dose": (0.0, 1.0),
    "nitidezza_dose": (0.0, 1.0),
}

VARIANTI: Final[tuple[str, ...]] = ("originale", "standard", "spinta")
PARAMETRI_VARIANTE: Final[dict[str, Parametri]] = {
    "standard": STANDARD,
    "spinta": SPINTA,
}
