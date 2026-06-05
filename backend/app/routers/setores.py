from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Setor, Tecnico
from app.routers.deps import get_current_tecnico
from app.schemas.schemas import SetorOut

router = APIRouter(prefix="/setores", tags=["setores"])


@router.get("", response_model=list[SetorOut])
def listar_setores(
    db: Session = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    return db.query(Setor).filter(Setor.ativo == True).order_by(Setor.nome).all()
