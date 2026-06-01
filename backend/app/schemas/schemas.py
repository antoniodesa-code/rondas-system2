from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# Auth
class LoginRequest(BaseModel):
    login: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tecnico_id: int
    nome: str


# Setor
class SetorOut(BaseModel):
    id: int
    nome: str
    ativo: bool

    model_config = {"from_attributes": True}


# Ronda
class RondaCreate(BaseModel):
    setor_id: int


class RondaUpdate(BaseModel):
    sistema_operante: Optional[bool] = None
    usuario_utilizando: Optional[bool] = None
    observacao: Optional[str] = None


class RondaOut(BaseModel):
    id: int
    setor_id: int
    setor_nome: str
    tecnico_id: int
    sistema_operante: Optional[bool]
    usuario_utilizando: Optional[bool]
    observacao: Optional[str]
    status: str
    criado_em: datetime

    model_config = {"from_attributes": True}


# QR
class QRGenerateRequest(BaseModel):
    ronda_id: int


class QRGenerateResponse(BaseModel):
    session_id: str
    url: str
    expires_in: int


class QRSessionInfo(BaseModel):
    setor_nome: str
    tecnico_nome: str


class QRConfirmRequest(BaseModel):
    resposta: str  # sim | nao
    device_data: Optional[dict] = None


class QRConfirmResponse(BaseModel):
    success: bool
    message: str


# Tecnico admin
class TecnicoCreate(BaseModel):
    nome: str
    login: str
    senha: str


class TecnicoOut(BaseModel):
    id: int
    nome: str
    login: str
    ativo: bool

    model_config = {"from_attributes": True}
