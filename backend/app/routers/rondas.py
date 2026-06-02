import base64
import io
import uuid
from datetime import datetime, timezone

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import delete_qr_session, get_qr_session, store_qr_session
from app.core.security import fingerprint_hash
from app.models.models import AuditoriaConfirmacao, Ronda, Setor, Tecnico
from app.routers.deps import get_current_tecnico
from app.schemas.schemas import (
    QRConfirmRequest,
    QRConfirmResponse,
    QRGenerateResponse,
    QRSessionInfo,
    RondaCreate,
    RondaOut,
    RondaUpdate,
)

router = APIRouter(prefix="/rondas", tags=["rondas"])


def _ronda_to_out(r: Ronda) -> RondaOut:
    return RondaOut(
        id=r.id,
        setor_id=r.setor_id,
        setor_nome=r.setor.nome,
        tecnico_id=r.tecnico_id,
        sistema_operante=r.sistema_operante,
        usuario_utilizando=r.usuario_utilizando,
        observacao=r.observacao,
        status=r.status,
        criado_em=r.criado_em,
    )


@router.post("", response_model=list[RondaOut], status_code=status.HTTP_201_CREATED)
async def iniciar_ronda(
    body: RondaCreate,
    db: AsyncSession = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    """Cria rondas para todos os setores ativos (ou um setor específico)."""
    if body.setor_id == 0:
        # Criar ronda para todos os setores ativos
        result = await db.execute(select(Setor).where(Setor.ativo == True).order_by(Setor.nome))
        setores = result.scalars().all()
    else:
        result = await db.execute(select(Setor).where(Setor.id == body.setor_id, Setor.ativo == True))
        setor = result.scalar_one_or_none()
        if not setor:
            raise HTTPException(status_code=404, detail="Setor não encontrado")
        setores = [setor]

    rondas = []
    for setor in setores:
        ronda = Ronda(setor_id=setor.id, tecnico_id=tecnico.id)
        db.add(ronda)
        rondas.append(ronda)

    await db.commit()

    # Recarregar com setor já incluído (eager load)
    ids = [r.id for r in rondas]
    result = await db.execute(
        select(Ronda).where(Ronda.id.in_(ids)).options(selectinload(Ronda.setor))
    )
    rondas_loaded = result.scalars().all()

    return [_ronda_to_out(r) for r in rondas_loaded]


@router.get("/hoje", response_model=list[RondaOut])
async def rondas_hoje(
    db: AsyncSession = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    """Retorna rondas do técnico criadas hoje."""
    hoje = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(Ronda)
        .join(Setor)
        .where(Ronda.tecnico_id == tecnico.id)
        .options(selectinload(Ronda.setor))
        .order_by(Setor.nome)
    )
    rondas = result.scalars().all()
    # Filtra pelo dia de hoje no Python para compatibilidade timezone
    rondas_hoje = [r for r in rondas if r.criado_em.date() == hoje]
    return [_ronda_to_out(r) for r in rondas_hoje]


@router.patch("/{ronda_id}", response_model=RondaOut)
async def atualizar_ronda(
    ronda_id: int,
    body: RondaUpdate,
    db: AsyncSession = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    result = await db.execute(
        select(Ronda)
        .join(Setor)
        .where(Ronda.id == ronda_id, Ronda.tecnico_id == tecnico.id)
        .options(selectinload(Ronda.setor))
    )
    ronda = result.scalar_one_or_none()
    if not ronda:
        raise HTTPException(status_code=404, detail="Ronda não encontrada")

    if body.sistema_operante is not None:
        ronda.sistema_operante = body.sistema_operante
    if body.usuario_utilizando is not None:
        ronda.usuario_utilizando = body.usuario_utilizando
    if body.observacao is not None:
        ronda.observacao = body.observacao

    await db.commit()
    await db.refresh(ronda)

    # Recarregar com setor após commit
    result2 = await db.execute(
        select(Ronda).where(Ronda.id == ronda.id).options(selectinload(Ronda.setor))
    )
    ronda = result2.scalar_one()
    return _ronda_to_out(ronda)


@router.post("/{ronda_id}/qr", response_model=QRGenerateResponse)
async def gerar_qr(
    ronda_id: int,
    db: AsyncSession = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    result = await db.execute(
        select(Ronda)
        .join(Setor)
        .where(Ronda.id == ronda_id, Ronda.tecnico_id == tecnico.id)
        .options(selectinload(Ronda.setor))
    )
    ronda = result.scalar_one_or_none()
    if not ronda:
        raise HTTPException(status_code=404, detail="Ronda não encontrada")

    session_id = str(uuid.uuid4())
    await store_qr_session(
        session_id,
        {
            "ronda_id": ronda.id,
            "setor_id": ronda.setor_id,
            "setor_nome": ronda.setor.nome,
            "tecnico_id": tecnico.id,
            "tecnico_nome": tecnico.nome,
        },
    )

    url = f"{settings.FRONTEND_URL}/confirm/{session_id}"
    return QRGenerateResponse(
        session_id=session_id,
        url=url,
        expires_in=settings.QR_EXPIRATION_SECONDS,
    )


@router.get("/{ronda_id}/qr/image")
async def qr_image(
    ronda_id: int,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    """Retorna o QR Code como imagem PNG em base64."""
    url = f"{settings.FRONTEND_URL}/confirm/{session_id}"
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return {"image_b64": encoded}


@router.get("/confirm/{session_id}/info", response_model=QRSessionInfo)
async def qr_info(session_id: str):
    """Retorna informações públicas da sessão QR (sem dados sensíveis)."""
    data = await get_qr_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="QR Code expirado ou inválido")
    return QRSessionInfo(setor_nome=data["setor_nome"], tecnico_nome=data["tecnico_nome"])


@router.post("/confirm/{session_id}", response_model=QRConfirmResponse)
async def confirmar_qr(
    session_id: str,
    body: QRConfirmRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Endpoint público — não requer login. Registra a confirmação do usuário do setor."""
    if body.resposta not in ("sim", "nao"):
        raise HTTPException(status_code=400, detail="Resposta inválida. Use 'sim' ou 'nao'")

    data = await get_qr_session(session_id)
    if not data:
        raise HTTPException(status_code=410, detail="QR Code expirado ou já utilizado")

    ronda_id = data["ronda_id"]
    result = await db.execute(select(Ronda).where(Ronda.id == ronda_id))
    ronda = result.scalar_one_or_none()
    if not ronda:
        raise HTTPException(status_code=404, detail="Ronda não encontrada")

    # Coleta de auditoria silenciosa
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    device_data = body.device_data or {}
    fp_hash = fingerprint_hash(device_data) if device_data else None

    import json
    auditoria = AuditoriaConfirmacao(
        ronda_id=ronda_id,
        ip=ip,
        user_agent=user_agent,
        fingerprint_hash=fp_hash,
        device_data=json.dumps(device_data) if device_data else None,
        resposta=body.resposta,
    )
    db.add(auditoria)

    ronda.status = "confirmado" if body.resposta == "sim" else "recusado"
    await db.commit()

    # Remove sessão do Redis após uso (one-time use)
    await delete_qr_session(session_id)

    return QRConfirmResponse(success=True, message="Resposta registrada com sucesso")
