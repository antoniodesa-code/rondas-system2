# Aqui concentro toda a comunicação com o Redis.
# Uso o Redis exclusivamente para armazenar as sessões temporárias dos QR Codes,
# aproveitando a expiração automática (TTL) que ele oferece nativamente.
# Assim não preciso criar nenhum job de limpeza — o Redis apaga sozinho quando o tempo expira.

import json

import redis.asyncio as aioredis

from app.core.config import settings

# Guardo a conexão em uma variável global para reutilizá-la entre as requisições.
# Criar uma nova conexão a cada request seria lento e desperdiçador de recursos.
_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Retorno a conexão existente com o Redis ou crio uma nova se ainda não existir.
    Uso o padrão singleton aqui para manter apenas uma conexão ativa durante toda a vida da aplicação."""
    global _redis
    if _redis is None:
        # Conecto usando a URL definida no .env e peço que as respostas venham como string (não bytes)
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def store_qr_session(session_id: str, data: dict, ttl: int = None) -> None:
    """Salvo aqui os dados da sessão do QR Code no Redis com tempo de expiração automático.
    Uso a chave no formato 'qr:{session_id}' para organizar e evitar colisão com outras chaves.
    O TTL padrão vem do .env (120 segundos) — após esse tempo o Redis apaga automaticamente,
    tornando o QR inválido sem que eu precise fazer nenhuma limpeza manual."""
    r = await get_redis()
    ttl = ttl or settings.QR_EXPIRATION_SECONDS
    # Serializo o dicionário como JSON antes de salvar, pois o Redis só aceita strings
    await r.setex(f"qr:{session_id}", ttl, json.dumps(data))


async def get_qr_session(session_id: str) -> dict | None:
    """Busco aqui os dados de uma sessão QR a partir do session_id.
    Se o QR já expirou ou nunca existiu, o Redis retorna None e eu repasso isso para quem chamou.
    Isso protege contra tentativas de uso de QR Codes expirados ou falsificados."""
    r = await get_redis()
    raw = await r.get(f"qr:{session_id}")
    if raw is None:
        return None
    # Deserializo o JSON de volta para dicionário Python antes de retornar
    return json.loads(raw)


async def delete_qr_session(session_id: str) -> None:
    """Apago manualmente a sessão QR do Redis após o usuário confirmar.
    Faço isso para garantir uso único — mesmo que o tempo ainda não tenha expirado,
    o QR não pode ser usado duas vezes. Isso evita que alguém escaneie o mesmo QR mais de uma vez."""
    r = await get_redis()
    await r.delete(f"qr:{session_id}")
