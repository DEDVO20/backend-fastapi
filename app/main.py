"""
Aplicación principal FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api import (
    routes, usuarios, procesos, documentos, 
    calidad, auditorias, riesgos, capacitaciones, sistema, auth, migraciones
)

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API construido con FastAPI para Sistema de Gestión de Calidad",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(sistema.router)
app.include_router(migraciones.router, prefix="/api/migraciones", tags=["migraciones"])


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




