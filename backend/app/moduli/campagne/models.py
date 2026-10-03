"""Tabelle dello sprint 1 (plan §2)."""
from datetime import date, datetime
from uuid import UUID
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Campagna(Base):
    __tablename__ = "campagna"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profilo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profilo_bottega.id"), nullable=False, index=True
    )
    titolo: Mapped[str] = mapped_column(Text, nullable=False)
    inizio: Mapped[date] = mapped_column(Date, nullable=False)
    fine: Mapped[date] = mapped_column(Date, nullable=False)
    descrizione: Mapped[str | None] = mapped_column(Text, nullable=True)
    crea_immagini_ai: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    stato: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    canali: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    frequenza: Mapped[str | None] = mapped_column(Text, nullable=True)
    obiettivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    profilo_snapshot: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    rimandata: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    inviata_il: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Foto(Base):
    __tablename__ = "foto"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profilo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profilo_bottega.id"), nullable=False
    )
    campagna_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=False, index=True
    )
    gruppo_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    origine: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'caricata'")
    )
    file: Mapped[str] = mapped_column(Text, nullable=False)
    mime: Mapped[str] = mapped_column(Text, nullable=False)
    larghezza: Mapped[int] = mapped_column(Integer, nullable=False)
    altezza: Mapped[int] = mapped_column(Integer, nullable=False)
    descrizione: Mapped[str | None] = mapped_column(Text, nullable=True)
    analisi_ai: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    n_utilizzi: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )


class DecisioneCampagna(Base):
    __tablename__ = "decisione_campagna"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campagna_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=False, index=True
    )
    utente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("utente.id"), nullable=False
    )
    esito: Mapped[str] = mapped_column(Text, nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    nota: Mapped[str | None] = mapped_column(Text, nullable=True)
    foto_segnate: Mapped[list[int] | None] = mapped_column(
        ARRAY(Integer), nullable=True
    )
    creata_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
