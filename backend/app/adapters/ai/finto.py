"""Provider AI finto per sviluppo e test: risposte prevedibili, nessuna rete."""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from functools import lru_cache
from io import BytesIO
from typing import Any

from PIL import Image

from app.core.orologio import ROMA

from .base import (
    TIPI_ERRORE,
    AIAdapter,
    CampagnaAI,
    ErroreAI,
    GruppoAI,
    PianoAI,
    PostAI,
    PostScritto,
    ImmagineAI,
    UsoAI,
)

PROVIDER = "finto"
MODELLO = "finto"
VERSIONE_PROMPT = "finto-1"

OPERAZIONI = ("analizza_gruppo", "pianifica_campagna", "genera_post", "genera_immagine")
ORA_DI_USCITA = time(10, 0)
# Il testo del post: la prima frase è quella di sempre, le altre servono alle rigenerazioni.
FRASI = (
    "{tema}. {nome} vi aspetta in bottega.",
    "{tema}: venite a scoprirlo da {nome}.",
    "Da {nome}: {tema}. Passate a trovarci.",
    "{nome} racconta: {tema}.",
)
TEMI_DEI_RIEMPITIVI = (
    "Dietro ogni pezzo c'è una storia",
    "Fatto a mano, con cura",
    "Il tempo giusto per fare le cose bene",
)
MESSAGGI = {
    "temporaneo": "Il servizio AI non ha risposto in tempo (errore simulato).",
    "risposta": "La risposta dell'AI non è nel formato chiesto (errore simulato).",
    "configurazione": "La chiave del servizio AI non è valida (errore simulato).",
    "richiesta": "La richiesta all'AI non è accettabile (errore simulato).",
    "rifiuto": "Il servizio AI ha rifiutato il contenuto (errore simulato).",
}


@dataclass
class _Errore:
    operazione: str
    tipo: str
    volte: int | None
    foto_id: int | None
    canale: str | None


@dataclass
class _Testo:
    testo: str
    hashtag: list[str]
    volte: int | None
    canale: str | None


class AIFinto(AIAdapter):
    """Provider simulato: lo stesso risultato a parità di dati.

    - Analisi: ogni foto è idonea e diversa dalle altre.
    - Piano: una foto per post, le foto disponibili dei limiti (già
      preselezionate, al massimo i post chiesti) nel loro ordine, poi i
      riempitivi `immagine_ai`, senza foto; date distribuite sul periodo,
      Instagram il giorno dopo Facebook.
    - Testo: una frase con il tema e il nome della bottega, due hashtag.

    Il resto si chiede a comando: ``carosello=True``, ``comanda_analisi()``,
    ``comanda_errore()``, ``comanda_piano_non_valido()``, ``comanda_testo()``.
    Ogni chiamata si registra in ``chiamate`` e lascia il suo ``ultimo_uso``,
    senza token e con il costo di ``costo_chiamata`` (0 se non si dice).
    """

    def __init__(
        self, *, carosello: bool = False, costo_chiamata: Decimal = Decimal(0)
    ) -> None:
        self.carosello = carosello
        self.costo_chiamata = costo_chiamata
        self.chiamate: list[dict[str, Any]] = []
        self._errori: list[_Errore] = []
        self._analisi: dict[int, dict[str, Any]] = {}
        self._testi: list[_Testo] = []
        self._piani_non_validi = 0

    # --- comandi ---------------------------------------------------------

    def comanda_errore(
        self,
        operazione: str,
        tipo: str,
        *,
        volte: int | None = 1,
        foto_id: int | None = None,
        canale: str | None = None,
    ) -> None:
        """Fa fallire ``operazione`` con un errore di ``tipo`` (R-35).

        ``volte`` conta le chiamate che falliscono; ``None`` vuol dire sempre.
        Con ``foto_id`` l'errore riguarda quella foto e scatta solo quando è
        tra le foto della chiamata; con ``canale`` solo sui post di quel canale.
        """
        if operazione not in OPERAZIONI:
            raise ValueError(f"Operazione AI non valida: {operazione}")
        if tipo not in TIPI_ERRORE:
            raise ValueError(f"Tipo di errore AI non valido: {tipo}")
        self._errori.append(_Errore(operazione, tipo, volte, foto_id, canale))

    def comanda_analisi(self, foto_id: int, **campi: Any) -> None:
        """Cambia l'analisi di una foto, per esempio ``idonea=False, motivo=…``."""
        self._analisi.setdefault(foto_id, {}).update(campi)

    def comanda_piano_non_valido(self, volte: int = 1) -> None:
        """Le prossime ``volte`` il piano esce senza l'ultima uscita."""
        self._piani_non_validi = volte

    def comanda_testo(
        self,
        testo: str,
        hashtag: Sequence[str] = (),
        *,
        volte: int | None = 1,
        canale: str | None = None,
    ) -> None:
        """Fa scrivere questo testo: vuoto, troppo lungo o con parole vietate."""
        self._testi.append(_Testo(testo, list(hashtag), volte, canale))

    def _uso(
        self,
        tipo: str,
        richiesta: Mapping[str, Any],
        risposta: Any = None,
        *,
        immagini: int | None = None,
    ) -> UsoAI:
        """L'uso di una chiamata riuscita, con lo storico di R-50 (durata 0)."""
        return UsoAI(
            tipo,
            PROVIDER,
            MODELLO,
            immagini=immagini,
            costo_usd=self.costo_chiamata,
            versione_prompt=VERSIONE_PROMPT,
            richiesta=dict(richiesta),
            risposta=(
                None
                if risposta is None
                else json.dumps(risposta, ensure_ascii=False, default=str)
            ),
            durata_ms=0,
        )

    def _solleva(
        self,
        operazione: str,
        tipo_uso: str,
        richiesta: Mapping[str, Any],
        *,
        foto: Sequence[int] = (),
        canale: str | None = None,
    ) -> None:
        for errore in self._errori:
            if errore.operazione != operazione or errore.volte == 0:
                continue
            if errore.foto_id is not None and errore.foto_id not in foto:
                continue
            if errore.canale is not None and errore.canale != canale:
                continue
            if errore.volte is not None:
                errore.volte -= 1
            sollevato = ErroreAI(
                errore.tipo, MESSAGGI[errore.tipo], foto_id=errore.foto_id
            )
            # Come l'adattatore vero: l'uso della chiamata fallita, prima dell'errore.
            sollevato.uso = self.ultimo_uso = UsoAI(
                tipo_uso,
                PROVIDER,
                MODELLO,
                versione_prompt=VERSIONE_PROMPT,
                richiesta=dict(richiesta),
                durata_ms=0,
                esito=errore.tipo,
                errore=f"{errore.tipo}: {MESSAGGI[errore.tipo]}",
            )
            raise sollevato

    # --- interfaccia -----------------------------------------------------

    def analizza_gruppo(self, gruppo: GruppoAI) -> dict[int, dict[str, Any]]:
        self.ultimo_uso = None
        ids = [foto.id for foto in gruppo.foto]
        chiamata = {"operazione": "analizza_gruppo", "gruppo": gruppo.id, "foto": ids}
        self.chiamate.append(chiamata)
        richiesta = {
            "descrizione_del_gruppo": gruppo.descrizione,
            "foto": [f"<foto {uno}>" for uno in ids],
        }
        self._solleva("analizza_gruppo", "analisi", richiesta, foto=ids)
        risultato = {}
        for foto in gruppo.foto:
            analisi = {
                "idonea": True,
                "simile_a": None,
                "tipo": "pezzo_finito",
                "punteggio": 0.8,
                "motivo": None,
                "soggetto": gruppo.descrizione or "Foto della bottega",
                "descrizione": gruppo.descrizione or "Foto della bottega",
                # Un riquadro al centro, metà della foto.
                "soggetto_box": {
                    "x": 0.25,
                    "y": 0.25,
                    "larghezza": 0.5,
                    "altezza": 0.5,
                },
            }
            analisi.update(self._analisi.get(foto.id, {}))
            risultato[foto.id] = analisi
        self.ultimo_uso = self._uso("analisi", richiesta, risultato)
        return risultato

    def pianifica_campagna(
        self,
        snapshot: Mapping[str, Any],
        campagna: CampagnaAI,
        gruppi: Sequence[GruppoAI],
        limiti: Mapping[str, Mapping[str, Any]],
        schede: Mapping[str, Mapping[str, Any]],
        *,
        non_prima_di: datetime,
        piano_precedente: Mapping[str, Any] | None = None,
        violazioni: Sequence[Mapping[str, Any]] | None = None,
    ) -> PianoAI:
        self.ultimo_uso = None
        chiamata = {
            "operazione": "pianifica_campagna",
            "riscrittura": piano_precedente is not None,
        }
        self.chiamate.append(chiamata)
        self._solleva("pianifica_campagna", "piano", chiamata)

        gruppo_della_foto = {
            foto.id: gruppo for gruppo in gruppi for foto in gruppo.foto
        }
        foto_del_canale = {
            canale: list(limite["foto_disponibili"])
            for canale, limite in limiti.items()
        }
        giorni = _giorni_utili(campagna.inizio, campagna.fine, non_prima_di)
        n_uscite = max(
            (limite["post_chiesti"] for limite in limiti.values()), default=0
        )

        uscite = []
        for indice in range(n_uscite):
            post = []
            gruppo = None
            for canale, limite in limiti.items():
                chiesti = limite["post_chiesti"]
                if indice >= chiesti:
                    continue
                disponibili = foto_del_canale[canale]
                foto = disponibili[indice : indice + 1]
                riempitivo = None
                if not foto:
                    # Finite le foto disponibili: un'immagine AI (R-28).
                    riempitivo = "immagine_ai"
                # Carosello a comando: solo dove non servono riempitivi (R-28)
                # e avanza una foto, che altrimenti resterebbe fuori dal piano.
                if (
                    self.carosello
                    and indice == 0
                    and limite["riempitivi"] == 0
                    and len(disponibili) > chiesti
                ):
                    foto = foto + [disponibili[chiesti]]
                if foto and gruppo is None:
                    gruppo = gruppo_della_foto.get(foto[0])
                sfasamento = 1 if canale == "instagram" and "facebook" in limiti else 0
                giorno = giorni[
                    min(indice * len(giorni) // n_uscite + sfasamento, len(giorni) - 1)
                ]
                post.append(
                    {
                        "canale": canale,
                        "formato": "carosello" if len(foto) > 1 else "singola",
                        "foto": foto,
                        "riempitivo": riempitivo,
                        "data_ora": datetime.combine(
                            giorno, ORA_DI_USCITA, tzinfo=ROMA
                        ).isoformat(),
                    }
                )
            if gruppo is not None:
                tema = gruppo.descrizione or "Le creazioni della bottega"
            else:
                tema = TEMI_DEI_RIEMPITIVI[indice % len(TEMI_DEI_RIEMPITIVI)]
            uscite.append(
                {
                    "numero": indice + 1,
                    "tema": tema,
                    "gruppo_id": gruppo.id if gruppo is not None else None,
                    "post": post,
                }
            )

        if self._piani_non_validi > 0:
            self._piani_non_validi -= 1
            uscite = uscite[:-1]
        nome = snapshot.get("nome") or "la bottega"
        strategia = (
            f"Raccontare {nome} con {n_uscite} uscite distribuite sul periodo: "
            f"prima le foto scelte dall'artigiano, poi le altre."
        )
        self.ultimo_uso = self._uso(
            "piano", chiamata, {"strategia": strategia, "uscite": uscite}
        )
        return PianoAI(
            contenuto={"strategia": strategia, "uscite": uscite},
            provider=PROVIDER,
            modello=MODELLO,
            versione_prompt=VERSIONE_PROMPT,
        )

    def genera_post(
        self,
        snapshot: Mapping[str, Any],
        campagna: CampagnaAI,
        post: PostAI,
        scheda: Mapping[str, Any],
        *,
        testo_precedente: str | None = None,
        violazioni: Sequence[Mapping[str, Any]] | None = None,
        versioni_rifiutate: Sequence[str] | None = None,
        testo_proposto: str | None = None,
        nota: str | None = None,
        altri_post: Sequence[str] | None = None,
    ) -> PostScritto:
        self.ultimo_uso = None
        chiamata = {
            "operazione": "genera_post",
            "canale": post.canale,
            "tema": post.tema,
            "riscrittura": testo_precedente is not None,
        }
        if post.immagine_ai:
            chiamata["immagine_ai"] = post.immagine_ai
        # Nelle rigenerazioni si vede che cosa è arrivato all'AI (R-04).
        if versioni_rifiutate:
            chiamata["rifiutate"] = list(versioni_rifiutate)
        if testo_proposto is not None:
            chiamata["testo_proposto"] = testo_proposto
        if nota:
            chiamata["nota"] = nota
        if altri_post:
            chiamata["altri_post"] = list(altri_post)
        self.chiamate.append(chiamata)
        self._solleva(
            "genera_post",
            "testo",
            chiamata,
            foto=[foto.id for foto in post.foto],
            canale=post.canale,
        )
        nome = snapshot.get("nome") or "La bottega"
        rifiutate = {uno.strip() for uno in versioni_rifiutate or []}
        if testo_proposto is not None:
            testo = testo_proposto.strip()
        else:
            # La prima frase che l'operatore non ha già scartato.
            frasi = [frase.format(tema=post.tema, nome=nome) for frase in FRASI]
            testo = next(
                (frase for frase in frasi if frase not in rifiutate),
                f"{frasi[0]} ({len(rifiutate)})",
            )
        hashtag = ["artigianato", "fattoamano"]
        for comandato in self._testi:
            if comandato.volte == 0:
                continue
            if comandato.canale is not None and comandato.canale != post.canale:
                continue
            if comandato.volte is not None:
                comandato.volte -= 1
            testo, hashtag = comandato.testo, list(comandato.hashtag)
            break
        self.ultimo_uso = self._uso(
            "testo", chiamata, {"testo": testo, "hashtag": hashtag}
        )
        return PostScritto(
            testo=testo,
            hashtag=hashtag,
            provider=PROVIDER,
            modello=MODELLO,
            versione_prompt=VERSIONE_PROMPT,
        )

    def genera_immagine(self, prompt: str) -> ImmagineAI:
        self.ultimo_uso = None
        chiamata = {"operazione": "genera_immagine", "prompt": prompt}
        self.chiamate.append(chiamata)
        self._solleva("genera_immagine", "immagine", chiamata)
        self.ultimo_uso = self._uso("immagine", chiamata, immagini=1)
        return ImmagineAI(
            contenuto=_immagine_fissa(),
            mime="image/png",
            provider=PROVIDER,
            modello=MODELLO,
            versione_prompt=VERSIONE_PROMPT,
        )


@lru_cache
def _immagine_fissa() -> bytes:
    """Lo stesso piccolo quadrato PNG, sempre: il finto non disegna nulla."""
    file = BytesIO()
    Image.new("RGB", (64, 64), (176, 92, 52)).save(file, "PNG")
    return file.getvalue()


def _giorni_utili(inizio: date, fine: date, non_prima_di: datetime) -> list[date]:
    """I giorni del periodo in cui un post delle 10 non esce prima del dovuto.

    Se non ne resta nessuno torna l'ultimo giorno: il piano non passerà il
    controllo delle date, e chi chiama lo saprà dal controllo.
    """
    giorni = [inizio + timedelta(days=n) for n in range((fine - inizio).days + 1)]
    utili = [
        giorno
        for giorno in giorni
        if datetime.combine(giorno, ORA_DI_USCITA, tzinfo=ROMA) >= non_prima_di
    ]
    return utili or giorni[-1:] or [fine]
