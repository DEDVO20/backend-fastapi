"""
API endpoints para gestión de migraciones de base de datos con Alembic.
"""
import os
import subprocess
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.migracion import (
    MigracionInfo,
    MigracionEstadoActual,
    MigracionListaResponse,
    MigracionOperacionRequest,
    MigracionOperacionResponse,
    MigracionHistorialItem
)
from ..models.usuario import Usuario
from .dependencies import get_current_user

router = APIRouter()

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Dependency para verificar que el usuario es administrador."""
    # Verificar si el usuario tiene rol de administrador
    # Asumiendo que existe una relación con roles
    if not any(ur.rol.nombre == "Administrador" for ur in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para esta operación"
        )
    return current_user


def ejecutar_comando_alembic(comando: List[str]) -> tuple[bool, str]:
    """
    Ejecuta un comando de Alembic y retorna el resultado.
    
    Args:
        comando: Lista con el comando y argumentos
        
    Returns:
        Tupla (success, output)
    """
    try:
        result = subprocess.run(
            comando,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout + result.stderr
        success = result.returncode == 0
        
        return success, output
    except subprocess.TimeoutExpired:
        return False, "El comando excedió el tiempo límite de ejecución"
    except Exception as e:
        return False, f"Error al ejecutar comando: {str(e)}"


def obtener_revision_actual() -> Optional[str]:
    """Obtiene la revisión actual de la base de datos."""
    success, output = ejecutar_comando_alembic(["alembic", "current"])
    
    if not success:
        return None
    
    # Parsear el output para obtener la revisión
    # Formato típico: "abc123 (head)"
    lines = output.strip().split('\n')
    for line in lines:
        if line.strip():
            parts = line.split()
            if parts:
                return parts[0]
    
    return None


def obtener_lista_migraciones() -> List[dict]:
    """Obtiene la lista de todas las migraciones disponibles."""
    success, output = ejecutar_comando_alembic(["alembic", "history"])
    
    if not success:
        return []
    
    migraciones = []
    lines = output.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('Rev:'):
            continue
            
        # Parsear líneas del formato: "abc123 -> def456, descripción"
        # o "abc123 (head), descripción"
        parts = line.split(',', 1)
        if len(parts) >= 1:
            revision_part = parts[0].strip()
            descripcion = parts[1].strip() if len(parts) > 1 else ""
            
            # Extraer revision
            revision_parts = revision_part.split()
            if revision_parts:
                revision = revision_parts[0]
                migraciones.append({
                    'revision': revision,
                    'descripcion': descripcion
                })
    
    return migraciones


def parsear_migraciones_desde_archivos() -> List[MigracionInfo]:
    """Lee los archivos de migración directamente para obtener información detallada."""
    versions_dir = BASE_DIR / "alembic" / "versions"
    
    if not versions_dir.exists():
        return []
    
    migraciones = []
    revision_actual = obtener_revision_actual()
    
    # Leer todos los archivos .py en el directorio versions
    for file_path in sorted(versions_dir.glob("*.py")):
        if file_path.name == "__init__.py":
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer información del archivo
            revision = None
            down_revision = None
            descripcion = ""
            
            for line in content.split('\n'):
                if line.strip().startswith('revision ='):
                    revision = line.split('=')[1].strip().strip('"\'')
                elif line.strip().startswith('down_revision ='):
                    down_revision = line.split('=')[1].strip().strip('"\'')
                    if down_revision == 'None':
                        down_revision = None
                elif '"""' in line and not descripcion:
                    # Extraer descripción del docstring
                    start = content.find('"""')
                    end = content.find('"""', start + 3)
                    if start != -1 and end != -1:
                        descripcion = content[start+3:end].strip()
            
            if revision:
                # Verificar si está aplicada comparando con la revisión actual
                aplicada = False
                if revision_actual:
                    aplicada = revision == revision_actual or self._es_ancestro(revision, revision_actual)
                
                migraciones.append(MigracionInfo(
                    revision=revision,
                    down_revision=down_revision,
                    descripcion=descripcion or file_path.stem,
                    fecha_creacion=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    aplicada=aplicada,
                    fecha_aplicacion=None  # No tenemos esta info sin una tabla de historial
                ))
        
        except Exception as e:
            print(f"Error al leer {file_path}: {e}")
            continue
    
    return migraciones


@router.get("/", response_model=MigracionListaResponse)
async def listar_migraciones(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todas las migraciones disponibles y su estado.
    """
    try:
        migraciones = parsear_migraciones_desde_archivos()
        revision_actual = obtener_revision_actual()
        
        total = len(migraciones)
        aplicadas = sum(1 for m in migraciones if m.aplicada)
        pendientes = total - aplicadas
        
        # Buscar descripción de la revisión actual
        descripcion_actual = None
        if revision_actual:
            for m in migraciones:
                if m.revision == revision_actual:
                    descripcion_actual = m.descripcion
                    break
        
        estado = MigracionEstadoActual(
            revision_actual=revision_actual,
            descripcion=descripcion_actual,
            total_migraciones=total,
            migraciones_aplicadas=aplicadas,
            migraciones_pendientes=pendientes,
            ultima_actualizacion=datetime.now()
        )
        
        return MigracionListaResponse(
            migraciones=migraciones,
            estado=estado
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener lista de migraciones: {str(e)}"
        )


@router.get("/current", response_model=MigracionEstadoActual)
async def obtener_estado_actual(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el estado actual de las migraciones de la base de datos.
    """
    try:
        migraciones = parsear_migraciones_desde_archivos()
        revision_actual = obtener_revision_actual()
        
        total = len(migraciones)
        aplicadas = sum(1 for m in migraciones if m.aplicada)
        pendientes = total - aplicadas
        
        descripcion_actual = None
        if revision_actual:
            for m in migraciones:
                if m.revision == revision_actual:
                    descripcion_actual = m.descripcion
                    break
        
        return MigracionEstadoActual(
            revision_actual=revision_actual,
            descripcion=descripcion_actual,
            total_migraciones=total,
            migraciones_aplicadas=aplicadas,
            migraciones_pendientes=pendientes,
            ultima_actualizacion=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado actual: {str(e)}"
        )


@router.get("/history")
async def obtener_historial(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el historial de migraciones.
    """
    try:
        success, output = ejecutar_comando_alembic(["alembic", "history", "--verbose"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener historial de migraciones"
            )
        
        return {
            "historial": output,
            "timestamp": datetime.now()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial: {str(e)}"
        )


@router.post("/upgrade", response_model=MigracionOperacionResponse)
async def aplicar_migraciones(
    request: MigracionOperacionRequest,
    current_user: Usuario = Depends(require_admin)
):
    """
    Aplica migraciones hasta la revisión especificada.
    Requiere permisos de administrador.
    """
    try:
        revision_anterior = obtener_revision_actual()
        
        # Ejecutar upgrade
        success, output = ejecutar_comando_alembic(["alembic", "upgrade", request.target])
        
        if not success:
            return MigracionOperacionResponse(
                success=False,
                message="Error al aplicar migraciones",
                revision_anterior=revision_anterior,
                revision_nueva=None,
                output=output
            )
        
        revision_nueva = obtener_revision_actual()
        
        return MigracionOperacionResponse(
            success=True,
            message=f"Migraciones aplicadas exitosamente hasta {request.target}",
            revision_anterior=revision_anterior,
            revision_nueva=revision_nueva,
            output=output
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al aplicar migraciones: {str(e)}"
        )


@router.post("/downgrade", response_model=MigracionOperacionResponse)
async def revertir_migraciones(
    request: MigracionOperacionRequest,
    current_user: Usuario = Depends(require_admin)
):
    """
    Revierte migraciones hasta la revisión especificada.
    Requiere permisos de administrador.
    """
    try:
        revision_anterior = obtener_revision_actual()
        
        # Ejecutar downgrade
        success, output = ejecutar_comando_alembic(["alembic", "downgrade", request.target])
        
        if not success:
            return MigracionOperacionResponse(
                success=False,
                message="Error al revertir migraciones",
                revision_anterior=revision_anterior,
                revision_nueva=None,
                output=output
            )
        
        revision_nueva = obtener_revision_actual()
        
        return MigracionOperacionResponse(
            success=True,
            message=f"Migraciones revertidas exitosamente hasta {request.target}",
            revision_anterior=revision_anterior,
            revision_nueva=revision_nueva,
            output=output
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al revertir migraciones: {str(e)}"
        )
