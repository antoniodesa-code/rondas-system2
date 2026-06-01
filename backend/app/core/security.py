import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def generate_qr_token(setor_id: int, tecnico_id: int, ronda_id: int) -> str:
    """Gera token HMAC-SHA256 para assinatura do QR."""
    timestamp = int(datetime.now(timezone.utc).timestamp())
    payload = f"{setor_id}:{tecnico_id}:{ronda_id}:{timestamp}"
    mac = hmac.new(settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256)
    return f"{payload}:{mac.hexdigest()}"


def fingerprint_hash(device_data: dict) -> str:
    """Gera SHA256 do fingerprint do dispositivo."""
    canonical = json.dumps(device_data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
