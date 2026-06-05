"""Script para criar tabelas e popular dados iniciais."""
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.models import Setor, Tecnico  # noqa: F401


def main():
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas.")

    db = SessionLocal()
    try:
        if not db.query(Tecnico).filter(Tecnico.login == "admin").first():
            admin = Tecnico(
                nome="Administrador",
                login="admin",
                senha_hash=hash_password("admin"),
            )
            db.add(admin)

        setores_iniciais = [
            "SAME", "AMBULATÓRIO", "ONCOLOGIA", "UTI", "PRONTO-SOCORRO",
            "FARMÁCIA", "LABORATÓRIO", "RADIOLOGIA", "CENTRO CIRÚRGICO", "MATERNIDADE",
        ]
        for nome in setores_iniciais:
            if not db.query(Setor).filter(Setor.nome == nome).first():
                db.add(Setor(nome=nome))

        db.commit()
        print("Dados iniciais inseridos.")
        print("Login: admin | Senha: admin")
    finally:
        db.close()


if __name__ == "__main__":
    main()
