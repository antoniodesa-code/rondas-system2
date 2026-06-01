"""Script para criar tabelas e popular dados iniciais."""
import asyncio
import platform

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
from sqlalchemy import text

from app.core.database import Base, engine
from app.core.security import hash_password
from app.models.models import Setor, Tecnico  # noqa: F401 — needed for metadata


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tabelas criadas.")

    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Verifica se já existe técnico admin
        from sqlalchemy import select
        result = await session.execute(select(Tecnico).where(Tecnico.login == "admin"))
        if not result.scalar_one_or_none():
            admin = Tecnico(
                nome="Administrador",
                login="admin",
                senha_hash=hash_password("admin"),
            )
            session.add(admin)

        # Setores iniciais
        setores_iniciais = [
            "SAME", "AMBULATÓRIO", "ONCOLOGIA", "UTI", "PRONTO-SOCORRO",
            "FARMÁCIA", "LABORATÓRIO", "RADIOLOGIA", "CENTRO CIRÚRGICO", "MATERNIDADE",
        ]
        for nome in setores_iniciais:
            result = await session.execute(select(Setor).where(Setor.nome == nome))
            if not result.scalar_one_or_none():
                session.add(Setor(nome=nome))

        await session.commit()
        print("Dados iniciais inseridos.")
        print("Login: admin | Senha: admin")


if __name__ == "__main__":
    asyncio.run(main())
