"""Tabelle dello sprint 1 (plan §2)."""
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base


class Post(Base):
    __tablename__ = "post"
    __table_args__ = (Index("ix_post_stato_data_ora", "stato", "data_ora"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campagna_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=False, index=True
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
    # Storico delle versioni, dalla prima all'ultima.
    versioni: Mapped[list["VersionePost"]] = relationship(
        order_by="VersionePost.numero", back_populates="post"
    )

    @property
    def versione_corrente(self) -> "VersionePost | None":
        """La versione corrente è l'ultima (plan §2)."""
        return self.versioni[-1] if self.versioni else None


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
    # Vuoti negli interventi senza AI (es. scelta_foto, sprint 3).
    provider_ai: Mapped[str | None] = mapped_column(Text, nullable=True)
    modello_ai: Mapped[str | None] = mapped_column(Text, nullable=True)
    versione_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    errori_validazione: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    creata_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    post: Mapped[Post] = relationship(back_populates="versioni")
