"""Tabelle dello sprint 1 (plan §2)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Approvazione(Base):
    __tablename__ = "approvazione"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    versione_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("versione_post.id"), nullable=False, index=True
    )
    utente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("utente.id"), nullable=False
    )
    ruolo: Mapped[str] = mapped_column(Text, nullable=False)
    esito: Mapped[str] = mapped_column(Text, nullable=False)
    creata_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
