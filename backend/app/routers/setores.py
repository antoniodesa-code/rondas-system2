# Aqui cuido da listagem dos setores do hospital.
# Por enquanto este router tem apenas uma rota — listar setores ativos —
# mas centralizei aqui para facilitar futuras expansões como edição e desativação de setores.

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Setor, Tecnico
from app.routers.deps import get_current_tecnico
from app.schemas.schemas import SetorOut

# Defino o prefixo /setores para todas as rotas deste router
router = APIRouter(prefix="/setores", tags=["setores"])


@router.get("", response_model=list[SetorOut])
async def listar_setores(
    db: AsyncSession = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),  # Uso _ porque não preciso dos dados do técnico, só verifico que está logado
):
    """Retorno aqui a lista de todos os setores ativos do hospital em ordem alfabética.
    Esta rota é protegida — somente técnicos logados conseguem acessá-la.
    O frontend usa esta lista para montar a tabela de ronda na tela principal.

    Retorno apenas setores com ativo=True para que setores desativados
    não apareçam na ronda sem precisar deletá-los do banco."""
    result = await db.execute(
        select(Setor)
        .where(Setor.ativo == True)   # Filtro apenas setores ativos
        .order_by(Setor.nome)          # Ordeno alfabeticamente para facilitar a leitura na tela
    )
    return result.scalars().all()
