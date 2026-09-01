"""Pruebas de configuración de la aplicación."""
from app.config import Settings


def test_cors_origins_se_convierte_en_lista():
    settings = Settings(
        CORS_ORIGINS="http://localhost:3000, http://localhost:5173,https://app.example.com"
    )
    assert settings.cors_origins_list == [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://app.example.com",
    ]


def test_valores_por_defecto_de_settings():
    settings = Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/db",
        SECRET_KEY="abc",
        SUPABASE_URL=None,
        SUPABASE_KEY=None,
    )
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert settings.SUPABASE_BUCKET == "imagenes"
