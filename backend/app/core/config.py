# Aqui centralizo todas as configurações do sistema que vêm do arquivo .env.
# Uso pydantic-settings para que cada variável seja lida automaticamente do ambiente,
# garantindo que nunca coloco senhas ou URLs sensíveis diretamente no código.

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # URL de conexão com o PostgreSQL — inclui usuário, senha, host e nome do banco
    DATABASE_URL: str

    # URL de conexão com o Redis — usado para armazenar sessões temporárias dos QR Codes
    REDIS_URL: str = "redis://localhost:6379/0"

    # Chave secreta usada para assinar os tokens JWT e os tokens HMAC do QR.
    # Nunca deve ser exposta ao frontend ou aparecer em logs.
    SECRET_KEY: str

    # Algoritmo de assinatura do JWT — uso HS256 (HMAC com SHA-256)
    ALGORITHM: str = "HS256"

    # Tempo de expiração do token de login do técnico (8 horas = 480 minutos)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Tempo de vida do QR Code em segundos — após 120s o Redis apaga automaticamente
    QR_EXPIRATION_SECONDS: int = 120

    # URL base do frontend — uso para montar o link que vai dentro do QR Code
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        # Digo ao pydantic para ler as variáveis do arquivo .env na raiz do backend
        env_file = ".env"


# Instancio as configurações uma única vez e importo este objeto em qualquer lugar do projeto
settings = Settings()
