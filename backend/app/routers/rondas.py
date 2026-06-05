import base64
import io
import json
import uuid
from datetime import datetime, timezone

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

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
def iniciar_ronda(
    body: RondaCreate,
    db: Session = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    if body.setor_id == 0:
        setores = db.query(Setor).filter(Setor.ativo == True).order_by(Setor.nome).all()
    else:
        setor = db.query(Setor).filter(Setor.id == body.setor_id, Setor.ativo == True).first()
        if not setor:
            raise HTTPException(status_code=404, detail="Setor não encontrado")
        setores = [setor]

    rondas = []
    for setor in setores:
        ronda = Ronda(setor_id=setor.id, tecnico_id=tecnico.id)
        db.add(ronda)
        rondas.append(ronda)

    db.commit()

    ids = [r.id for r in rondas]
    rondas_loaded = (
        db.query(Ronda)
        .options(joinedload(Ronda.setor))
        .filter(Ronda.id.in_(ids))
        .all()
    )

    return [_ronda_to_out(r) for r in rondas_loaded]


@router.get("/hoje", response_model=list[RondaOut])
def rondas_hoje(
    db: Session = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    hoje = datetime.now(timezone.utc).date()

    rondas = (
        db.query(Ronda)
        .options(joinedload(Ronda.setor))
        .filter(Ronda.tecnico_id == tecnico.id)
        .order_by(Setor.nome)
        .join(Setor)
        .all()
    )

    rondas_hoje = [r for r in rondas if r.criado_em.date() == hoje]
    return [_ronda_to_out(r) for r in rondas_hoje]


@router.patch("/{ronda_id}", response_model=RondaOut)
def atualizar_ronda(
    ronda_id: int,
    body: RondaUpdate,
    db: Session = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    ronda = (
        db.query(Ronda)
        .options(joinedload(Ronda.setor))
        .filter(Ronda.id == ronda_id, Ronda.tecnico_id == tecnico.id)
        .first()
    )
    if not ronda:
        raise HTTPException(status_code=404, detail="Ronda não encontrada")

    if body.sistema_operante is not None:
        ronda.sistema_operante = body.sistema_operante
    if body.usuario_utilizando is not None:
        ronda.usuario_utilizando = body.usuario_utilizando
    if body.observacao is not None:
        ronda.observacao = body.observacao

    db.commit()
    db.refresh(ronda)
    return _ronda_to_out(ronda)


@router.post("/{ronda_id}/qr", response_model=QRGenerateResponse)
def gerar_qr(
    ronda_id: int,
    db: Session = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    ronda = (
        db.query(Ronda)
        .options(joinedload(Ronda.setor))
        .filter(Ronda.id == ronda_id, Ronda.tecnico_id == tecnico.id)
        .first()
    )
    if not ronda:
        raise HTTPException(status_code=404, detail="Ronda não encontrada")

    session_id = str(uuid.uuid4())

    store_qr_session(
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
def qr_image(
    ronda_id: int,
    session_id: str,
    db: Session = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    url = f"{settings.FRONTEND_URL}/confirm/{session_id}"
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return {"image_b64": encoded}


@router.get("/confirm/{session_id}/info", response_model=QRSessionInfo)
def qr_info(session_id: str):
    data = get_qr_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="QR Code expirado ou inválido")
    return QRSessionInfo(setor_nome=data["setor_nome"], tecnico_nome=data["tecnico_nome"])


@router.post("/confirm/{session_id}", response_model=QRConfirmResponse)
def confirmar_qr(
    session_id: str,
    body: QRConfirmRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    if body.resposta not in ("sim", "nao"):
        raise HTTPException(status_code=400, detail="Resposta inválida. Use 'sim' ou 'nao'")

    data = get_qr_session(session_id)
    if not data:
        raise HTTPException(status_code=410, detail="QR Code expirado ou já utilizado")

    ronda_id = data["ronda_id"]
    ronda = db.query(Ronda).filter(Ronda.id == ronda_id).first()
    if not ronda:
        raise HTTPException(status_code=404, detail="Ronda não encontrada")

    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    device_data = body.device_data or {}
    fp_hash = fingerprint_hash(device_data) if device_data else None

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
    db.commit()

    delete_qr_session(session_id)

    return QRConfirmResponse(success=True, message="Resposta registrada com sucesso")
