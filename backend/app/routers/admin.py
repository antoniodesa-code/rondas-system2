from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import Setor, Tecnico
from app.routers.deps import get_current_tecnico
from app.schemas.schemas import SetorOut, TecnicoCreate, TecnicoOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/tecnicos", response_model=TecnicoOut, status_code=status.HTTP_201_CREATED)
def criar_tecnico(
    body: TecnicoCreate,
    db: Session = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    if db.query(Tecnico).filter(Tecnico.login == body.login).first():
        raise HTTPException(status_code=400, detail="Login já existe")

    tecnico = Tecnico(
        nome=body.nome,
        login=body.login,
        senha_hash=hash_password(body.senha)
    )
    db.add(tecnico)
    db.commit()
    db.refresh(tecnico)
    return tecnico


@router.get("/tecnicos", response_model=list[TecnicoOut])
def listar_tecnicos(
    db: Session = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    return db.query(Tecnico).order_by(Tecnico.nome).all()


@router.post("/setores", response_model=SetorOut, status_code=status.HTTP_201_CREATED)
def criar_setor(
    nome: str,
    db: Session = Depends(get_db),
    _: Tecnico = Depends(get_current_tecnico),
):
    setor = Setor(nome=nome.upper())
    db.add(setor)
    db.commit()
    db.refresh(setor)
    return setor
