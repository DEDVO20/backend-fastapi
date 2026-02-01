"""
Aplicación principal FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api import (
    routes, usuarios, procesos, documentos, 
    calidad, auditorias, riesgos, capacitaciones, competencias, sistema, auth, migraciones, tickets, notificaciones,
    analytics
)

app = FastAPI(
    title="Sistema de Gestión de Calidad",
    description="API para sistema de gestión de calidad ISO 9001",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... (omitted)

# Incluir routers
app.include_router(auth.router)
app.include_router(routes.router)
app.include_router(usuarios.router)
app.include_router(procesos.router)
app.include_router(documentos.router)
app.include_router(calidad.router)
app.include_router(auditorias.router)
app.include_router(riesgos.router)
app.include_router(capacitaciones.router)
app.include_router(competencias.router)
app.include_router(sistema.router)
app.include_router(migraciones.router, prefix="/api/migraciones", tags=["migraciones"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(notificaciones.router)
app.include_router(analytics.router)


@app.on_event("startup")
async def startup_event():
    """Evento que se ejecuta al iniciar la aplicación"""
    print(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📝 Documentación disponible en: http://localhost:8000/docs")
    print(f"🌍 Entorno: {settings.ENVIRONMENT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento que se ejecuta al cerrar la aplicación"""
    print("👋 Cerrando aplicación...")




