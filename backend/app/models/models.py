from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def now_utc():
    return datetime.now(timezone.utc)


class Setor(Base):
    __tablename__ = "setores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    rondas: Mapped[list["Ronda"]] = relationship(back_populates="setor")


class Tecnico(Base):
    __tablename__ = "tecnicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    login: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    rondas: Mapped[list["Ronda"]] = relationship(back_populates="tecnico")


class Ronda(Base):
    __tablename__ = "rondas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    setor_id: Mapped[int] = mapped_column(ForeignKey("setores.id"), nullable=False)
    tecnico_id: Mapped[int] = mapped_column(ForeignKey("tecnicos.id"), nullable=False)
    sistema_operante: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    usuario_utilizando: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Status: pendente | confirmado | recusado
    status: Mapped[str] = mapped_column(String(20), default="pendente")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    setor: Mapped["Setor"] = relationship(back_populates="rondas")
    tecnico: Mapped["Tecnico"] = relationship(back_populates="rondas")
    auditoria: Mapped[list["AuditoriaConfirmacao"]] = relationship(back_populates="ronda")


class AuditoriaConfirmacao(Base):
    __tablename__ = "auditoria_confirmacao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ronda_id: Mapped[int] = mapped_column(ForeignKey("rondas.id"), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    fingerprint_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    resposta: Mapped[str] = mapped_column(String(10), nullable=False)  # sim | nao
    confirmado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
