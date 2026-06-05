import asyncio
import platform

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Usa psycopg2 (driver síncrono) — compatível com Windows + Docker Desktop
_sync_url = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
).replace(
    "postgresql+psycopg://", "postgresql+psycopg2://"
)

engine = create_engine(_sync_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
