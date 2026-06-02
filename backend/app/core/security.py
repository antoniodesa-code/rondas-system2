# Aqui concentro toda a lógica de segurança do sistema:
# hashing de senhas, geração e validação de tokens JWT, assinatura HMAC e fingerprint de dispositivos.

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Configuro o contexto de hashing de senhas usando bcrypt.
# O bcrypt é ideal porque é lento por design — dificulta ataques de força bruta.
# O parâmetro deprecated="auto" faz com que senhas antigas sejam re-hasheadas automaticamente.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    """Uso esta função para verificar se a senha digitada pelo técnico bate com o hash salvo no banco.
    Nunca comparo as senhas diretamente — sempre passo pelo bcrypt para evitar comparações inseguras."""
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    """Uso esta função ao cadastrar um técnico para transformar a senha em hash antes de salvar no banco.
    Assim, mesmo que o banco vaze, ninguém consegue ver as senhas reais."""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Gero aqui o token JWT que o técnico recebe ao fazer login.
    Coloco dentro dele o ID e o nome do técnico, mais uma data de expiração.
    Assino o token com a SECRET_KEY para garantir que ninguém pode falsificá-lo."""
    to_encode = data.copy()
    # Defino quando o token vai expirar — por padrão 8 horas após o login
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Assino e retorno o token no formato compacto JWT (três partes separadas por ponto)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Uso esta função para ler e validar o token JWT que vem no header de cada requisição.
    Se o token for inválido, adulterado ou expirado, retorno None para negar o acesso."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        # Retorno None silenciosamente — quem chamou decide como tratar a negação
        return None


def generate_qr_token(setor_id: int, tecnico_id: int, ronda_id: int) -> str:
    """Fiz isso porque gero um token HMAC-SHA256 que permite verificar assinaturas
    recalculando o MAC e comparando-o de forma segura para assinatura do QR.
    O HMAC garante que o token não pode ser forjado sem a SECRET_KEY do servidor."""
    timestamp = int(datetime.now(timezone.utc).timestamp())
    # Junto os dados relevantes em um payload separado por dois pontos
    payload = f"{setor_id}:{tecnico_id}:{ronda_id}:{timestamp}"
    # Assino o payload com HMAC-SHA256 usando a chave secreta do servidor
    mac = hmac.new(settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256)
    # Retorno o payload junto com a assinatura — o backend pode verificar recalculando o MAC
    return f"{payload}:{mac.hexdigest()}"


def fingerprint_hash(device_data: dict) -> str:
    """Gero aqui um hash SHA256 dos dados do dispositivo coletados silenciosamente pelo frontend.
    Uso isso para criar uma impressão digital única do dispositivo que confirmou a ronda,
    permitindo detectar no futuro se o mesmo dispositivo confirmou rondas suspeitas em sequência.
    Os dados são ordenados antes do hash para garantir que a ordem dos campos não mude o resultado."""
    canonical = json.dumps(device_data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
