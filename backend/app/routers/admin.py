# Aqui cuido das operações administrativas do sistema.
# Estas rotas são usadas para gerenciar técnicos e setores — operações que só
# um técnico autenticado pode realizar. No futuro posso adicionar um nível de permissão
# separado (ex: admin vs técnico comum), mas por ora qualquer técnico logado tem acesso.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import Setor, Tecnico
from app.routers.deps import get_current_tecnico
from app.schemas.schemas import SetorOut, TecnicoCreate, TecnicoOut

# Defino o prefixo /admin para separar visualmente estas rotas das operações comuns
router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/tecnicos", response_model=TecnicoOut, status_code=status.HTTP_201_CREATED)
async def criar_tecnico(
    body: TecnicoCreate,
    db: AsyncSession = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    """Crio aqui um novo técnico no sistema.
    Antes de inserir, verifico se o login já existe no banco para evitar duplicatas,
    pois o login deve ser único — é o identificador de acesso de cada técnico.
    A senha é transformada em hash bcrypt antes de salvar — nunca salvo senha em texto puro."""

    # Verifico se já existe um técnico com esse login para evitar conflito
    result = await db.execute(select(Tecnico).where(Tecnico.login == body.login))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Login já existe")

    # Crio o técnico com a senha já hasheada — o campo senha_hash nunca recebe texto puro
    tecnico = Tecnico(
        nome=body.nome,
        login=body.login,
        senha_hash=hash_password(body.senha)
    )
    db.add(tecnico)
    await db.commit()
    await db.refresh(tecnico)  # Atualizo o objeto para incluir o ID gerado pelo banco
    return tecnico


@router.get("/tecnicos", response_model=list[TecnicoOut])
async def listar_tecnicos(
    db: AsyncSession = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    """Listo aqui todos os técnicos cadastrados no sistema, ativos e inativos.
    Uso isso na área administrativa para visualizar e gerenciar a equipe de técnicos.
    O campo senha_hash nunca é retornado — o schema TecnicoOut não o inclui propositalmente."""
    result = await db.execute(select(Tecnico).order_by(Tecnico.nome))
    return result.scalars().all()


@router.post("/setores", response_model=SetorOut, status_code=status.HTTP_201_CREATED)
async def criar_setor(
    nome: str,
    db: AsyncSession = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    """Crio aqui um novo setor hospitalar no sistema.
    Converto o nome para maiúsculas automaticamente para manter padronização visual
    na tabela de rondas — assim não fica misturado 'Same', 'SAME', 'same'."""
    setor = Setor(nome=nome.upper())
    db.add(setor)
    await db.commit()
    await db.refresh(setor)  # Atualizo o objeto para pegar o ID gerado pelo banco
    return setor
