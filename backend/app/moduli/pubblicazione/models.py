"""Tabelle dello sprint 1 (plan §2)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Pubblicazione(Base):
    __tablename__ = "pubblicazione"
    __table_args__ = (
        Index(
            "uq_pubblicazione_ok_post",
            "post_id",
            unique=True,
            postgresql_where=text("stato = 'ok'"),
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("post.id"), nullable=False)
    versione_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("versione_post.id"), nullable=False
    )
    n_tentativo: Mapped[int] = mapped_column(Integer, nullable=False)
    stato: Mapped[str] = mapped_column(Text, nullable=False)
    id_esterno: Mapped[str | None] = mapped_column(Text, nullable=True)
    errore: Mapped[str | None] = mapped_column(Text, nullable=True)
    creata_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
