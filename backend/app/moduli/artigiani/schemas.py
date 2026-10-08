"""Stato pubblico dei canali, senza permessi o identificativi social."""

from pydantic import BaseModel


class CanaleCollegato(BaseModel):
    canale: str
    collegato: bool
