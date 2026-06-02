# Aqui cuido de tudo relacionado ao login dos técnicos.
# Apenas técnicos têm login — usuários do setor nunca passam por aqui.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.models import Tecnico
from app.schemas.schemas import LoginRequest, TokenResponse

# Defino o prefixo /auth para todas as rotas deste router
# e o tag "auth" para agrupar no Swagger (/docs)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Processo aqui o login do técnico.
    Recebo login e senha, verifico no banco, valido a senha com bcrypt
    e retorno um token JWT que o frontend vai guardar e usar em todas as próximas requisições.

    Uso uma mensagem de erro genérica ("Credenciais inválidas") propositalmente —
    não informo se foi o login ou a senha que errou, para dificultar ataques de enumeração de usuários.
    """
    # Busco o técnico pelo login e verifico se ele está ativo —
    # técnicos desativados não devem conseguir entrar mesmo com a senha correta
    result = await db.execute(
        select(Tecnico).where(Tecnico.login == body.login, Tecnico.ativo == True)
    )
    tecnico = result.scalar_one_or_none()

    # Se o técnico não existe ou a senha não bate com o hash salvo no banco, nego o acesso
    if not tecnico or not verify_password(body.senha, tecnico.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    # Gero o token JWT com o ID e nome do técnico embutidos dentro dele.
    # O frontend vai guardar este token e mandá-lo no header Authorization de cada requisição.
    token = create_access_token({"sub": str(tecnico.id), "nome": tecnico.nome})

    return TokenResponse(access_token=token, tecnico_id=tecnico.id, nome=tecnico.nome)
