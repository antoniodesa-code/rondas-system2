from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import admin, auth, rondas, setores

app = FastAPI(
    title="Ronda Hospitalar API",
    description="Sistema de ronda hospitalar com auditoria e QR Code",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(setores.router)
app.include_router(rondas.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
