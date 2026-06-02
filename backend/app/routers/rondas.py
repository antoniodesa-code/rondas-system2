# Aqui fica o coração do sistema — toda a lógica de rondas hospitalares.
# Este router controla: criação das rondas do dia, atualização de status por setor,
# geração de QR Codes temporários e o registro de confirmações dos usuários dos setores.

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

# Defino o prefixo /rondas para todas as rotas deste router
router = APIRouter(prefix="/rondas", tags=["rondas"])


def _ronda_to_out(r: Ronda) -> RondaOut:
    """Converto aqui um objeto Ronda do banco em um RondaOut para retornar ao frontend.
    Faço isso em uma função separada para não repetir a conversão em cada endpoint.
    Incluo o nome do setor diretamente no retorno — o frontend não precisa fazer uma segunda chamada."""
    return RondaOut(
        id=r.id,
        setor_id=r.setor_id,
        setor_nome=r.setor.nome,       # Acesso o nome do setor já carregado via selectinload
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
    """Inicio aqui a ronda do dia para o técnico logado.
    Quando setor_id=0, crio uma ronda para todos os setores ativos de uma vez —
    isso é o comportamento padrão ao clicar em 'Iniciar Ronda de Hoje'.
    Quando setor_id é específico, crio a ronda apenas para aquele setor.

    Após salvar no banco, recarrego as rondas com selectinload para trazer o nome do setor
    de forma eficiente em uma única query, evitando o erro de lazy loading no contexto async."""

    if body.setor_id == 0:
        # Busco todos os setores ativos em ordem alfabética para criar uma ronda para cada um
        result = await db.execute(
            select(Setor).where(Setor.ativo == True).order_by(Setor.nome)
        )
        setores = result.scalars().all()
    else:
        # Busco apenas o setor específico informado
        result = await db.execute(
            select(Setor).where(Setor.id == body.setor_id, Setor.ativo == True)
        )
        setor = result.scalar_one_or_none()
        if not setor:
            raise HTTPException(status_code=404, detail="Setor não encontrado")
        setores = [setor]

    # Crio um objeto Ronda para cada setor e adiciono todos de uma vez na sessão
    rondas = []
    for setor in setores:
        ronda = Ronda(setor_id=setor.id, tecnico_id=tecnico.id)
        db.add(ronda)
        rondas.append(ronda)

    # Salvo todas as rondas no banco em uma única transação
    await db.commit()

    # Recarrego as rondas com selectinload para incluir os dados do setor relacionado.
    # Uso selectinload aqui porque o SQLAlchemy async não permite lazy loading fora de contexto assíncrono.
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
    """Retorno aqui as rondas que o técnico logado criou hoje.
    O frontend chama este endpoint ao entrar na tela principal para saber se já existe
    uma ronda iniciada — evitando que o técnico crie rondas duplicadas no mesmo dia.

    Faço o filtro por data no Python (não no SQL) para lidar corretamente com fusos horários,
    comparando sempre com a data UTC atual."""

    hoje = datetime.now(timezone.utc).date()

    # Busco todas as rondas do técnico com o setor já carregado em uma única query
    result = await db.execute(
        select(Ronda)
        .join(Setor)
        .where(Ronda.tecnico_id == tecnico.id)
        .options(selectinload(Ronda.setor))  # Carrego o setor junto para evitar lazy loading
        .order_by(Setor.nome)
    )
    rondas = result.scalars().all()

    # Filtro no Python apenas as rondas criadas hoje — compatível com qualquer timezone
    rondas_hoje = [r for r in rondas if r.criado_em.date() == hoje]

    return [_ronda_to_out(r) for r in rondas_hoje]


@router.patch("/{ronda_id}", response_model=RondaOut)
async def atualizar_ronda(
    ronda_id: int,
    body: RondaUpdate,
    db: AsyncSession = Depends(get_db),
    tecnico: Tecnico = Depends(get_current_tecnico),
):
    """Atualizo aqui os campos de uma ronda específica — sistema operante, usuário utilizando e observação.
    Verifico que a ronda pertence ao técnico logado antes de permitir a edição,
    para garantir que um técnico não consiga alterar rondas de outro técnico.

    Uso PATCH (não PUT) porque o frontend envia apenas os campos que mudaram,
    não o objeto inteiro — isso torna a atualização mais eficiente."""

    # Busco a ronda garantindo que ela pertence ao técnico logado
    result = await db.execute(
        select(Ronda)
        .join(Setor)
        .where(Ronda.id == ronda_id, Ronda.tecnico_id == tecnico.id)
        .options(selectinload(Ronda.setor))
    )
    ronda = result.scalar_one_or_none()
    if not ronda:
        raise HTTPException(status_code=404, detail="Ronda não encontrada")

    # Atualizo apenas os campos que foram enviados — None significa "não alterar"
    if body.sistema_operante is not None:
        ronda.sistema_operante = body.sistema_operante
    if body.usuario_utilizando is not None:
        ronda.usuario_utilizando = body.usuario_utilizando
    if body.observacao is not None:
        ronda.observacao = body.observacao

    await db.commit()

    # Recarrego a ronda com o setor após o commit para garantir dados atualizados
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
    """Gero aqui o QR Code temporário para o técnico mostrar ao usuário do setor.
    Crio um session_id único (UUID), salvo os dados da sessão no Redis com TTL de 120 segundos
    e retorno a URL que ficará dentro do QR — ao escanear, o usuário abre essa URL.

    O QR não contém dados sensíveis — apenas o session_id. Os dados reais ficam no Redis,
    protegidos no servidor e inacessíveis pelo QR."""

    # Verifico que a ronda existe e pertence ao técnico logado antes de gerar o QR
    result = await db.execute(
        select(Ronda)
        .join(Setor)
        .where(Ronda.id == ronda_id, Ronda.tecnico_id == tecnico.id)
        .options(selectinload(Ronda.setor))
    )
    ronda = result.scalar_one_or_none()
    if not ronda:
        raise HTTPException(status_code=404, detail="Ronda não encontrada")

    # Gero um ID único para esta sessão QR — cada clique gera um novo QR diferente
    session_id = str(uuid.uuid4())

    # Salvo no Redis os dados necessários para processar a confirmação quando o QR for escaneado.
    # O TTL (tempo de vida) é de 120 segundos — após isso o Redis apaga automaticamente.
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

    # Monto a URL que vai dentro do QR — o usuário do setor vai abrir esta URL ao escanear
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
    """Gero aqui a imagem do QR Code como PNG codificado em base64.
    O frontend recebe o base64 e exibe diretamente como uma tag <img src="data:image/png;base64,..."/>.
    Dessa forma não preciso salvar nenhum arquivo no servidor — tudo fica em memória."""

    # Monto a URL que vai codificada dentro do QR Code
    url = f"{settings.FRONTEND_URL}/confirm/{session_id}"

    # Gero a imagem do QR e a salvo em memória como PNG
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    # Converto os bytes para base64 string para que o frontend possa usar em uma tag <img>
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return {"image_b64": encoded}


@router.get("/confirm/{session_id}/info", response_model=QRSessionInfo)
async def qr_info(session_id: str):
    """Retorno aqui as informações públicas da sessão QR para exibir na tela de confirmação.
    Quando o usuário do setor escaneia o QR, o frontend chama este endpoint para mostrar
    'Técnico X compareceu ao setor Y?' — sem expor nenhum dado sensível.

    Este endpoint é público — não requer login — porque é acessado pelo celular do usuário do setor."""
    data = await get_qr_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="QR Code expirado ou inválido")
    # Retorno apenas nome do setor e nome do técnico — nada sensível vai para o frontend público
    return QRSessionInfo(setor_nome=data["setor_nome"], tecnico_nome=data["tecnico_nome"])


@router.post("/confirm/{session_id}", response_model=QRConfirmResponse)
async def confirmar_qr(
    session_id: str,
    body: QRConfirmRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Processo aqui a confirmação do usuário do setor após escanear o QR Code.
    Este é o único endpoint público do sistema — não exige login porque é o usuário comum do hospital.

    O fluxo é:
    1. Valido que o QR ainda existe no Redis (não expirou)
    2. Busco a ronda no banco pelo ronda_id guardado na sessão Redis
    3. Coleto silenciosamente dados do dispositivo para auditoria antifraude
    4. Salvo a resposta (sim/não) na tabela de auditoria
    5. Atualizo o status da ronda para confirmado/recusado
    6. Apago o QR do Redis para garantir uso único

    A auditoria silenciosa registra IP, user agent e fingerprint do dispositivo
    sem exibir nada ao usuário — serve apenas para rastreabilidade interna."""

    # Valido que a resposta é exatamente "sim" ou "nao" — nada além disso é aceito
    if body.resposta not in ("sim", "nao"):
        raise HTTPException(status_code=400, detail="Resposta inválida. Use 'sim' ou 'nao'")

    # Verifico se o QR ainda existe no Redis — se não existir, ele expirou ou já foi usado
    data = await get_qr_session(session_id)
    if not data:
        raise HTTPException(status_code=410, detail="QR Code expirado ou já utilizado")

    # Busco a ronda no banco usando o ronda_id que guardei na sessão Redis
    ronda_id = data["ronda_id"]
    result = await db.execute(select(Ronda).where(Ronda.id == ronda_id))
    ronda = result.scalar_one_or_none()
    if not ronda:
        raise HTTPException(status_code=404, detail="Ronda não encontrada")

    # Coleto dados para auditoria silenciosa — o usuário do setor não sabe que isso acontece.
    # O IP pode vir do header X-Forwarded-For quando há um proxy ou load balancer na frente.
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")  # Identifica o navegador e sistema operacional
    device_data = body.device_data or {}
    # Gero o hash SHA256 dos dados do dispositivo para criar a impressão digital única
    fp_hash = fingerprint_hash(device_data) if device_data else None

    import json
    # Salvo todos os dados de auditoria na tabela auditoria_confirmacao para rastreabilidade futura
    auditoria = AuditoriaConfirmacao(
        ronda_id=ronda_id,
        ip=ip,
        user_agent=user_agent,
        fingerprint_hash=fp_hash,
        device_data=json.dumps(device_data) if device_data else None,  # Salvo como JSON string
        resposta=body.resposta,
    )
    db.add(auditoria)

    # Atualizo o status da ronda com base na resposta do usuário
    # — "confirmado" se clicou SIM, "recusado" se clicou NÃO
    ronda.status = "confirmado" if body.resposta == "sim" else "recusado"
    await db.commit()

    # Apago o QR do Redis imediatamente após o uso — garanto que não pode ser usado uma segunda vez
    # mesmo que o tempo de 120 segundos ainda não tenha expirado
    await delete_qr_session(session_id)

    return QRConfirmResponse(success=True, message="Resposta registrada com sucesso")
