"""Tabelle dello sprint 1 (plan §2)."""
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
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


class Post(Base):
    __tablename__ = "post"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campagna_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=False
    )
    canale: Mapped[str] = mapped_column(Text, nullable=False)
    data_ora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stato: Mapped[str] = mapped_column(Text, nullable=False)
    da_rivedere: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    n_rigenerazioni_testo: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )


class VersionePost(Base):
    __tablename__ = "versione_post"
    __table_args__ = (
        UniqueConstraint("post_id", "numero", name="uq_versione_post_numero"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("post.id"), nullable=False)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    testo: Mapped[str] = mapped_column(Text, nullable=False)
    hashtag: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    foto_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("foto.id"), nullable=True
    )
    tipo_intervento: Mapped[str] = mapped_column(Text, nullable=False)
    testo_proposto: Mapped[str | None] = mapped_column(Text, nullable=True)
    nota: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_ai: Mapped[str] = mapped_column(Text, nullable=False)
    modello_ai: Mapped[str] = mapped_column(Text, nullable=False)
    versione_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    errori_validazione: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    creata_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
