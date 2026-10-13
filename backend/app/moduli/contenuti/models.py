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


class Piano(Base):
    """Piano di pubblicazione scritto dall'AI (plan §2)."""

    __tablename__ = "piano"
    __table_args__ = (
        UniqueConstraint("campagna_id", "numero", name="uq_piano_numero"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campagna_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=False
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    strategia: Mapped[str] = mapped_column(Text, nullable=False)
    contenuto: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    esito_controllo: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    debole: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    provider_ai: Mapped[str | None] = mapped_column(Text, nullable=True)
    modello_ai: Mapped[str | None] = mapped_column(Text, nullable=True)
    versione_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    creata_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class Uscita(Base):
    """Un'uscita della campagna: un tema per canale in una data (plan §2)."""

    __tablename__ = "uscita"
    __table_args__ = (
        UniqueConstraint("campagna_id", "numero", name="uq_uscita_numero"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campagna_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=False
    )
    gruppo_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("gruppo_foto.id"), nullable=True
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    tema: Mapped[str] = mapped_column(Text, nullable=False)


class Post(Base):
    __tablename__ = "post"
    __table_args__ = (
        Index("ix_post_stato_data_ora", "stato", "data_ora"),
        UniqueConstraint("uscita_id", "canale", name="uq_post_uscita_canale"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campagna_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=False, index=True
    )
    uscita_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("uscita.id"), nullable=False
    )
    canale: Mapped[str] = mapped_column(Text, nullable=False)
    formato: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'singola'")
    )
    riempitivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_ora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stato: Mapped[str] = mapped_column(Text, nullable=False)
    da_rivedere: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    n_rigenerazioni_testo: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    controllato_da: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("utente.id"), nullable=True
    )
    controllato_il: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    intervento_in_corso: Mapped[str | None] = mapped_column(Text, nullable=True)
    intervento_dal: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    autore_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("utente.id"), nullable=True
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
    legami_foto: Mapped[list["VersionePostFoto"]] = relationship(
        order_by="VersionePostFoto.posizione"
    )


class VersionePostFoto(Base):
    """Foto di una versione del post, in ordine (plan §2)."""

    __tablename__ = "versione_post_foto"
    __table_args__ = (
        UniqueConstraint(
            "versione_id", "posizione", name="uq_versione_post_foto_posizione"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    versione_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("versione_post.id"), nullable=False
    )
    posizione: Mapped[int] = mapped_column(Integer, nullable=False)
    foto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("foto.id"), nullable=False, index=True
    )


class ErroreGenerazione(Base):
    """Errore registrato durante la generazione della campagna (plan §2, R-24)."""

    __tablename__ = "errore_generazione"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campagna_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    messaggio: Mapped[str] = mapped_column(Text, nullable=False)
    tappa: Mapped[str] = mapped_column(Text, nullable=False)
    canale: Mapped[str | None] = mapped_column(Text, nullable=True)
    creata_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
