"""Provider AI finto per sviluppo e test: risposte prevedibili, nessuna rete."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

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
)

PROVIDER = "finto"
MODELLO = "finto"
VERSIONE_PROMPT = "finto-1"

OPERAZIONI = ("analizza_gruppo", "pianifica_campagna", "genera_post")
ORA_DI_USCITA = time(10, 0)
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
    - Piano: una foto per post, le foto con la stella per prime, tutte le foto
      disponibili fino ai post chiesti, poi i riempitivi: prima le foto
      d'archivio già uscite sul canale, poi le cartoline; date distribuite
      sul periodo, Instagram il giorno dopo Facebook.
    - Testo: una frase con il tema e il nome della bottega, due hashtag.

    Il resto si chiede a comando: ``carosello=True``, ``comanda_analisi()``,
    ``comanda_errore()``, ``comanda_piano_non_valido()``, ``comanda_testo()``.
    Ogni chiamata si registra in ``chiamate``.
    """

    def __init__(self, *, carosello: bool = False) -> None:
        self.carosello = carosello
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

    def _solleva(
        self,
        operazione: str,
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
            raise ErroreAI(errore.tipo, MESSAGGI[errore.tipo], foto_id=errore.foto_id)

    # --- interfaccia -----------------------------------------------------

    def analizza_gruppo(self, gruppo: GruppoAI) -> dict[int, dict[str, Any]]:
        ids = [foto.id for foto in gruppo.foto]
        self.chiamate.append(
            {"operazione": "analizza_gruppo", "gruppo": gruppo.id, "foto": ids}
        )
        self._solleva("analizza_gruppo", foto=ids)
        risultato = {}
        for foto in gruppo.foto:
            analisi = {
                "idonea": True,
                "simile_a": None,
                "tipo": "pezzo_finito",
                "punteggio": 0.8,
                "motivo": None,
                "soggetto": gruppo.descrizione or "Foto della bottega",
            }
            analisi.update(self._analisi.get(foto.id, {}))
            risultato[foto.id] = analisi
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
        self.chiamate.append(
            {
                "operazione": "pianifica_campagna",
                "riscrittura": piano_precedente is not None,
            }
        )
        self._solleva("pianifica_campagna")

        gruppo_della_foto = {
            foto.id: gruppo for gruppo in gruppi for foto in gruppo.foto
        }
        stelle = {foto.id for gruppo in gruppi for foto in gruppo.foto if foto.da_usare}
        # Le foto con la stella per prime: così entrano sempre nel piano (R-23).
        foto_del_canale = {
            canale: sorted(limite["foto_disponibili"], key=lambda f: f not in stelle)
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
                    # Finite le foto disponibili: una foto d'archivio già
                    # uscita sul canale, poi le cartoline (R-28).
                    manca = indice - len(disponibili)
                    foto = list(limite["foto_riempitivo"][manca : manca + 1])
                    riempitivo = "archivio" if foto else "cartolina"
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
    ) -> PostScritto:
        self.chiamate.append(
            {
                "operazione": "genera_post",
                "canale": post.canale,
                "tema": post.tema,
                "riscrittura": testo_precedente is not None,
            }
        )
        self._solleva(
            "genera_post", foto=[foto.id for foto in post.foto], canale=post.canale
        )
        nome = snapshot.get("nome") or "La bottega"
        testo = f"{post.tema}. {nome} vi aspetta in bottega."
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
        return PostScritto(
            testo=testo,
            hashtag=hashtag,
            provider=PROVIDER,
            modello=MODELLO,
            versione_prompt=VERSIONE_PROMPT,
        )


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
