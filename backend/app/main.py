# Aqui defino o ponto de entrada da aplicação FastAPI.
# É neste arquivo que junto todas as peças do sistema: middlewares, routers e configurações globais.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import admin, auth, rondas, setores

# Crio a instância principal da API com título e versão que aparecerão no Swagger (/docs)
app = FastAPI(
    title="Ronda Hospitalar API",
    description="Sistema de ronda hospitalar com auditoria e QR Code",
    version="1.0.0",
)

# Adiciono o middleware de CORS para permitir que o frontend (React/Vite) acesse a API.
# Sem isso o navegador bloquearia todas as requisições vindas de outro endereço (ex: localhost:5173).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,  # Permito cookies e headers de autenticação
    allow_methods=["*"],     # Permito todos os métodos HTTP (GET, POST, PATCH, DELETE...)
    allow_headers=["*"],     # Permito todos os headers, incluindo Authorization com o token JWT
)

# Registro cada grupo de rotas na aplicação.
# Cada router cuida de uma responsabilidade diferente do sistema.
app.include_router(auth.router)    # Login e autenticação dos técnicos
app.include_router(setores.router) # Listagem dos setores do hospital
app.include_router(rondas.router)  # Criação, atualização e QR Code das rondas
app.include_router(admin.router)   # Gerenciamento de técnicos e setores (área administrativa)


@app.get("/health")
async def health():
    """Criei este endpoint simples para verificar se a API está no ar.
    É útil para monitoramento e para confirmar que o servidor subiu corretamente."""
    return {"status": "ok"}
