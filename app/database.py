"""
Configuración de la base de datos con SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Motor de base de datos
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verificar conexión antes de usarla
    pool_size=10,        # Número de conexiones en el pool
    max_overflow=20      # Conexiones adicionales permitidas
)

# Sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obtener sesión de base de datos.
    Usar con FastAPI Depends.
    """
    if (settings.ENVIRONMENT or "").lower() != "test":
        try:
            from .db.ensure_schema import asegurar_esquema_login

            asegurar_esquema_login()
        except Exception as exc:
            print(f"⚠️ No se pudo asegurar el esquema de login: {exc}")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
