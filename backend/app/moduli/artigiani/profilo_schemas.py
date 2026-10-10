"""Dati del profilo: valori del dominio, nessun identificativo scrivibile."""
from datetime import datetime
from math import isfinite
from typing import Any

from pydantic import BaseModel, ConfigDict, JsonValue, ValidationInfo, field_validator

from . import domain


def verifica_testi(valore: Any) -> None:
    if isinstance(valore, str):
        if "\x00" in valore:
            raise ValueError("Caratteri non validi.")
        try:
            valore.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Caratteri non validi.") from None
    elif isinstance(valore, float) and not isfinite(valore):
        raise ValueError("Numero non valido.")
    elif isinstance(valore, dict):
        for chiave, elemento in valore.items():
            verifica_testi(chiave)
            verifica_testi(elemento)
    elif isinstance(valore, list):
        for elemento in valore:
            verifica_testi(elemento)


class DatiProfilo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    referente: str
    citta: str
    tipo_prodotto: str
    clienti_ideali: str
    obiettivo: str
    canali: list[str]
    anni_attivita: int | None = None
    sito: str | None = None
    storia: str | None = None
    origine: str | None = None
    valori: list[str] | None = None
    gamma: str | None = None
    fascia_prezzo: str | None = None
    stagionalita: str | None = None
    zona: str | None = None
    tono: list[str] | None = None
    cortesia: str | None = None
    vincoli: str | None = None
    frequenza: str | None = None
    orari: dict[str, JsonValue] | list[JsonValue] | None = None
    social_esistenti: dict[str, JsonValue] | None = None
    foto_policy: dict[str, JsonValue] | None = None
    eventi_ricorrenti: list[dict[str, JsonValue]] | None = None
    chiusure: str | None = None


class ProfiloScrittura(DatiProfilo):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    @field_validator("*", mode="before")
    @classmethod
    def testi_sicuri(cls, valore: Any) -> Any:
        verifica_testi(valore)
        return valore

    @field_validator("nome", "referente", "citta", "clienti_ideali")
    @classmethod
    def obbligatori(cls, valore: str) -> str:
        if not valore:
            raise ValueError("Campo obbligatorio.")
        return valore

    @field_validator("anni_attivita")
    @classmethod
    def anni_validi(cls, valore: int | None) -> int | None:
        if valore is not None and not 0 <= valore <= 2147483647:
            raise ValueError("Anni di attività non validi.")
        return valore

    @field_validator(
        "tipo_prodotto", "obiettivo", "fascia_prezzo", "cortesia", "frequenza"
    )
    @classmethod
    def scelta_valida(cls, valore: str | None, info: ValidationInfo) -> str | None:
        ammessi = {
            "tipo_prodotto": domain.TIPI_PRODOTTO,
            "obiettivo": domain.OBIETTIVI,
            "fascia_prezzo": domain.FASCE_PREZZO,
            "cortesia": domain.CORTESIE,
            "frequenza": domain.FREQUENZE,
        }
        if valore is not None and valore not in ammessi[info.field_name]:
            raise ValueError("Valore non ammesso.")
        return valore

    @field_validator("canali", "valori", "tono")
    @classmethod
    def scelte_valide(
        cls, valore: list[str] | None, info: ValidationInfo
    ) -> list[str] | None:
        ammessi = {
            "canali": domain.CANALI,
            "valori": domain.VALORI,
            "tono": domain.TONI,
        }
        if info.field_name == "canali" and not valore:
            raise ValueError("Selezionare almeno un canale.")
        if valore is not None and (
            len(valore) != len(set(valore))
            or any(v not in ammessi[info.field_name] for v in valore)
        ):
            raise ValueError("Selezione non valida.")
        return valore

    @field_validator("foto_policy")
    @classmethod
    def policy_valida(cls, valore: dict | None) -> dict | None:
        if valore is None:
            return None
        ammessi = {
            "quantita_mese": domain.FOTO_QUANTITA_MESE,
            "chi_scatta": domain.FOTO_CHI_SCATTA,
            "persone": domain.FOTO_PERSONE,
        }
        if any(k not in ammessi or v not in ammessi[k] for k, v in valore.items()):
            raise ValueError("Politica foto non valida.")
        return valore

    @field_validator("social_esistenti")
    @classmethod
    def social_validi(cls, valore: dict | None) -> dict | None:
        if valore is None:
            return None
        if set(valore) - {"canali", "profili", "cosa_funziona"}:
            raise ValueError("Social esistenti non validi.")
        canali = valore.get("canali", [])
        if not isinstance(canali, list) or any(
            c not in domain.CANALI_SOCIAL_ESISTENTI for c in canali
        ):
            raise ValueError("Social esistenti non validi.")
        if len(canali) != len(set(canali)) or ("nessuno" in canali and len(canali) > 1):
            raise ValueError("Social esistenti non validi.")
        if any(
            not isinstance(valore[k], str)
            for k in ("profili", "cosa_funziona")
            if k in valore
        ):
            raise ValueError("Social esistenti non validi.")
        return valore

    @field_validator("eventi_ricorrenti")
    @classmethod
    def eventi_validi(cls, valore: list[dict] | None) -> list[dict] | None:
        for evento in valore or []:
            if (
                set(evento) != {"nome", "quando", "tipo"}
                or evento["tipo"] not in domain.TIPI_EVENTO
            ):
                raise ValueError("Evento ricorrente non valido.")
            if any(
                not isinstance(evento[k], str) or not evento[k].strip()
                for k in ("nome", "quando")
            ):
                raise ValueError("Evento ricorrente non valido.")
        return valore


class ProfiloPubblico(DatiProfilo):
    id: int
    logo: str | None = None
    aggiornato_il: datetime
