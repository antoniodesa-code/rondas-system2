# Aqui defino as dependências reutilizáveis da API.
# O FastAPI tem um sistema de injeção de dependências — uso isso para centralizar
# a lógica de autenticação e reutilizá-la em qualquer endpoint que precise de um técnico logado.

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import Tecnico

# Crio o extrator de token Bearer — ele lê automaticamente o header "Authorization: Bearer <token>"
# em cada requisição e passa o token para a função de autenticação.
bearer = HTTPBearer()


async def get_current_tecnico(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> Tecnico:
    """Uso esta dependência como porteiro de todos os endpoints protegidos.
    Ela extrai o token JWT do header, valida a assinatura e busca o técnico no banco.
    Se qualquer coisa falhar — token inválido, expirado ou técnico desativado —
    retorno 401 Unauthorized e o endpoint nem chega a executar.

    Para usar em um endpoint, basta adicionar: tecnico: Tecnico = Depends(get_current_tecnico)
    """
    # Decodifico o token JWT e verifico se a assinatura é válida e se ainda não expirou
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )

    # Extraio o ID do técnico que coloquei dentro do token no momento do login
    tecnico_id = int(payload["sub"])

    # Busco o técnico no banco — verifico também se ele ainda está ativo,
    # pois um técnico pode ser desativado mesmo com o token ainda válido
    result = await db.execute(
        select(Tecnico).where(Tecnico.id == tecnico_id, Tecnico.ativo == True)
    )
    tecnico = result.scalar_one_or_none()

    if not tecnico:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Técnico não encontrado"
        )

    # Retorno o objeto técnico completo para que o endpoint possa usá-lo diretamente
    return tecnico
