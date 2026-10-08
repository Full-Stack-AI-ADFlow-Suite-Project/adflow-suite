"""Tabelle dello sprint 1 (plan §2)."""
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Utente(Base):
    __tablename__ = "utente"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    ruolo: Mapped[str] = mapped_column(Text, nullable=False)
    attivo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    deve_cambiare_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )


class Sessione(Base):
    __tablename__ = "sessione"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    utente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("utente.id"), nullable=False, index=True
    )
    scade_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LimiteLogin(Base):
    __tablename__ = "limite_login"
    __table_args__ = (
        CheckConstraint("tentativi > 0", name="limite_login_tentativi_positivi"),
    )
    chiave: Mapped[str] = mapped_column(String(64), primary_key=True)
    tentativi: Mapped[int] = mapped_column(Integer, nullable=False)
    scade_il: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
