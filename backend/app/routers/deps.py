from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import Tecnico

bearer = HTTPBearer()


async def get_current_tecnico(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> Tecnico:
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

    tecnico_id = int(payload["sub"])
    result = await db.execute(select(Tecnico).where(Tecnico.id == tecnico_id, Tecnico.ativo == True))
    tecnico = result.scalar_one_or_none()
    if not tecnico:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Técnico não encontrado")
    return tecnico
