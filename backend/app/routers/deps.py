from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import Tecnico

bearer = HTTPBearer()


def get_current_tecnico(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Tecnico:
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )

    tecnico_id = int(payload["sub"])
    tecnico = db.query(Tecnico).filter(
        Tecnico.id == tecnico_id, Tecnico.ativo == True
    ).first()

    if not tecnico:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Técnico não encontrado"
        )

    return tecnico
