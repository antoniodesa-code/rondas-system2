from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.models import Tecnico
from app.schemas.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    tecnico = db.query(Tecnico).filter(
        Tecnico.login == body.login, Tecnico.ativo == True
    ).first()

    if not tecnico or not verify_password(body.senha, tecnico.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    token = create_access_token({"sub": str(tecnico.id), "nome": tecnico.nome})
    return TokenResponse(access_token=token, tecnico_id=tecnico.id, nome=tecnico.nome)
