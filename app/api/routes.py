"""
Rutas de la API
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import settings

router = APIRouter()


@router.get("/")
async def root():
    """Endpoint raíz de bienvenida"""
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "environment": settings.ENVIRONMENT
    }


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Intentar ejecutar una consulta simple para verificar la conexión a la DB
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    otp_schema = False
    try:
        from ..db.ensure_schema import otp_disponible

        otp_schema = otp_disponible()
    except Exception:
        otp_schema = False

    return {
        "status": "ok",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "codigos_automaticos": True,
        "adjuntos_sin_requests": True,
        "otp_schema": otp_schema,
    }


@router.get("/api/v1/items")
async def get_items():
    """Endpoint de ejemplo para listar items"""
    return {
        "items": [
            {"id": 1, "name": "Item 1", "description": "Descripción del item 1"},
            {"id": 2, "name": "Item 2", "description": "Descripción del item 2"},
            {"id": 3, "name": "Item 3", "description": "Descripción del item 3"}
        ],
        "total": 3
    }
