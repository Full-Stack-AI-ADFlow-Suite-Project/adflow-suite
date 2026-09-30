from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Utente(Base):
    __tablename__ = "utente"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    ruolo: Mapped[str] = mapped_column(String(50), nullable=False)  # artigiano, operatore, admin
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creato_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.utcnow())

    sessioni: Mapped[list["Sessione"]] = relationship(back_populates="utente", cascade="all, delete-orphan")


class Sessione(Base):
    __tablename__ = "sessione"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    utente_id: Mapped[int] = mapped_column(ForeignKey("utente.id"), nullable=False)
    scade_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    creata_il: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.utcnow())

    utente: Mapped["Utente"] = relationship(back_populates="sessioni")
