from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Setor, Tecnico
from app.routers.deps import get_current_tecnico
from app.schemas.schemas import SetorOut

router = APIRouter(prefix="/setores", tags=["setores"])


@router.get("", response_model=list[SetorOut])
async def listar_setores(
    db: AsyncSession = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    result = await db.execute(select(Setor).where(Setor.ativo == True).order_by(Setor.nome))
    return result.scalars().all()
