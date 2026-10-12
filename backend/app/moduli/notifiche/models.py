"""Tabelle dello sprint 2b (plan §2)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Notifica(Base):
    """Una notifica per destinatario: l'email parte dal job ``invia_notifica``."""

    __tablename__ = "notifica"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    utente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("utente.id"), nullable=False, index=True
    )
    campagna_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campagna.id"), nullable=False, index=True
    )
    # Solo per le notifiche di un post (``post_fallito``): distingue gli eventi.
    post_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("post.id"), nullable=True
    )
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    canale: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'email'")
    )
    stato_invio: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'da_inviare'")
    )
    creata_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    inviata_il: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
