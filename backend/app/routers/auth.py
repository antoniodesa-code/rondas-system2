from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.models import Tecnico
from app.schemas.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tecnico).where(Tecnico.login == body.login, Tecnico.ativo == True))
    tecnico = result.scalar_one_or_none()

    if not tecnico or not verify_password(body.senha, tecnico.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    token = create_access_token({"sub": str(tecnico.id), "nome": tecnico.nome})
    return TokenResponse(access_token=token, tecnico_id=tecnico.id, nome=tecnico.nome)
