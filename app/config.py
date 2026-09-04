"""
Configuración de la aplicación usando Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Información de la aplicación
    APP_NAME: str = "FastAPI Backend"
    APP_VERSION: str = "1.2.13"
    
    # Base de datos
    DATABASE_URL: str = "postgresql://fastapi_user:fastapi_password@localhost:5432/fastapi_db"
    
    # Seguridad
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_INTENTOS: int = 5
    OTP_REENVIO_SEGUNDOS: int = 60
    # Temporal: Gmail/Outlook hasta definir el dominio institucional.
    # Solo Gmail u Outlook para crear usuarios y enviar OTP.
    CORREOS_INSTITUCIONALES: str = "gmail.com,outlook.com,hotmail.com,live.com"

    # Correo remitente del OTP. La contraseña SMTP no se guarda en el código:
    # debe ir en variables de entorno del servidor (SMTP_PASSWORD).
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = "calidad.iudc@gmail.com"
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = "calidad.iudc@gmail.com"
    SMTP_USE_TLS: bool = True
    # Render bloquea SMTP. OTP por HTTPS: Brevo (cualquier destinatario) o Resend.
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM: Optional[str] = "SGC Calidad <beth.t@example.com>"
    BREVO_API_KEY: Optional[str] = None
    BREVO_FROM: Optional[str] = "calidad.iudc@gmail.com"
    
    # Entorno
    ENVIRONMENT: str = "development"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://front-react-puce-three.vercel.app"
    
    # Supabase Storage
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_BUCKET: str = "imagenes"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convierte CORS_ORIGINS string a lista"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Permitir variables adicionales sin error


# Instancia global de configuración
settings = Settings()
