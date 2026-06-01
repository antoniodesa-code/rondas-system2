from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import Setor, Tecnico
from app.routers.deps import get_current_tecnico
from app.schemas.schemas import SetorOut, TecnicoCreate, TecnicoOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/tecnicos", response_model=TecnicoOut, status_code=status.HTTP_201_CREATED)
async def criar_tecnico(
    body: TecnicoCreate,
    db: AsyncSession = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    result = await db.execute(select(Tecnico).where(Tecnico.login == body.login))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Login já existe")

    tecnico = Tecnico(nome=body.nome, login=body.login, senha_hash=hash_password(body.senha))
    db.add(tecnico)
    await db.commit()
    await db.refresh(tecnico)
    return tecnico


@router.get("/tecnicos", response_model=list[TecnicoOut])
async def listar_tecnicos(
    db: AsyncSession = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    result = await db.execute(select(Tecnico).order_by(Tecnico.nome))
    return result.scalars().all()


@router.post("/setores", response_model=SetorOut, status_code=status.HTTP_201_CREATED)
async def criar_setor(
    nome: str,
    db: AsyncSession = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    setor = Setor(nome=nome.upper())
    db.add(setor)
    await db.commit()
    await db.refresh(setor)
    return setor
