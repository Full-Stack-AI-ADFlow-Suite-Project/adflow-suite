"""Tabelle dello sprint 1 (plan §2)."""
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
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
    stato: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    canali: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    canali_tolti: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    frequenza: Mapped[str | None] = mapped_column(Text, nullable=True)
    obiettivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    profilo_snapshot: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    inviata_il: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    chiusa_il: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class GruppoFoto(Base):
    """Gruppo di foto, legato a una campagna o riusabile dall'archivio."""

    __tablename__ = "gruppo_foto"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profilo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profilo_bottega.id"), nullable=False, index=True
    )
    campagna_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=True, index=True
    )
    origine: Mapped[str] = mapped_column(Text, nullable=False)
    descrizione: Mapped[str | None] = mapped_column(Text, nullable=True)
    da_usare_il: Mapped[date | None] = mapped_column(Date, nullable=True)
    n_immagini: Mapped[int | None] = mapped_column(Integer, nullable=True)

    foto: Mapped[list["Foto"]] = relationship(order_by="Foto.id")


class Foto(Base):
    __tablename__ = "foto"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profilo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profilo_bottega.id"), nullable=False
    )
    campagna_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=True, index=True
    )
    gruppo_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("gruppo_foto.id"), nullable=True, index=True
    )
    origine: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'caricata'")
    )
    file: Mapped[str] = mapped_column(Text, nullable=False)
    mime: Mapped[str] = mapped_column(Text, nullable=False)
    larghezza: Mapped[int] = mapped_column(Integer, nullable=False)
    altezza: Mapped[int] = mapped_column(Integer, nullable=False)
    da_usare: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
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
    canale: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("post.id"), nullable=True
    )
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
