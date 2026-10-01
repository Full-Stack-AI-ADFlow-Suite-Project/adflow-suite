from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.db import Base

class Utente(Base):
    __tablename__ = "utenti"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nome = Column(String, nullable=True)
    ruolo = Column(String, default="artigiano")
    attivo = Column(Boolean, default=True)
    creato_il = Column(DateTime(timezone=True), server_default=func.now())

class Sessione(Base):
    __tablename__ = "sessioni"
    id = Column(Integer, primary_key=True, index=True)
    utente_id = Column(Integer, ForeignKey("utenti.id"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False)
    scade_il = Column(DateTime(timezone=True), nullable=False)
