"""Tabelle dello sprint 1 (plan §2)."""
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class ProfiloBottega(Base):
    __tablename__ = "profilo_bottega"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    utente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("utente.id"), nullable=False, unique=True
    )
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    referente: Mapped[str] = mapped_column(Text, nullable=False)
    citta: Mapped[str] = mapped_column(Text, nullable=False)
    anni_attivita: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sito: Mapped[str | None] = mapped_column(Text, nullable=True)
    storia: Mapped[str | None] = mapped_column(Text, nullable=True)
    origine: Mapped[str | None] = mapped_column(Text, nullable=True)
    valori: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    tipo_prodotto: Mapped[str] = mapped_column(Text, nullable=False)
    gamma: Mapped[str | None] = mapped_column(Text, nullable=True)
    fascia_prezzo: Mapped[str | None] = mapped_column(Text, nullable=True)
    stagionalita: Mapped[str | None] = mapped_column(Text, nullable=True)
    clienti_ideali: Mapped[str] = mapped_column(Text, nullable=False)
    obiettivo: Mapped[str] = mapped_column(Text, nullable=False)
    zona: Mapped[str | None] = mapped_column(Text, nullable=True)
    tono: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    cortesia: Mapped[str | None] = mapped_column(Text, nullable=True)
    vincoli: Mapped[str | None] = mapped_column(Text, nullable=True)
    canali: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    frequenza: Mapped[str | None] = mapped_column(Text, nullable=True)
    orari: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    social_esistenti: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    foto_policy: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    eventi_ricorrenti: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    chiusure: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo: Mapped[str | None] = mapped_column(Text, nullable=True)
    aggiornato_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class AccountSocial(Base):
    """Account social collegato al profilo della bottega (plan §2)."""

    __tablename__ = "account_social"
    __table_args__ = (
        UniqueConstraint(
            "profilo_id", "piattaforma", name="uq_account_social_piattaforma"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profilo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profilo_bottega.id"), nullable=False
    )
    piattaforma: Mapped[str] = mapped_column(Text, nullable=False)
    id_pagina: Mapped[str | None] = mapped_column(Text, nullable=True)
    permesso: Mapped[str | None] = mapped_column(Text, nullable=True)
    scadenza: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    stato: Mapped[str] = mapped_column(Text, nullable=False)
