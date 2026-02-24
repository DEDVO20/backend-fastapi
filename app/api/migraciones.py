"""
API endpoints para gestion de migraciones de base de datos con Alembic.
"""
import ast
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, status

from ..models.usuario import Usuario
from ..schemas.migracion import (
    MigracionEstadoActual,
    MigracionInfo,
    MigracionListaResponse,
    MigracionOperacionRequest,
    MigracionOperacionResponse,
)
from .dependencies import get_current_user

router = APIRouter()

# Ruta base del proyecto backend-fastapi
BASE_DIR = Path(__file__).resolve().parent.parent.parent
REVISION_RE = re.compile(r"^revision(?:\s*:[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
DOWN_REVISION_RE = re.compile(r"^down_revision(?:\s*:[^=]+)?\s*=\s*(.+)$", re.MULTILINE)
DOCSTRING_RE = re.compile(r'"""(.*?)"""', re.DOTALL)


def _permisos_usuario(current_user: Usuario) -> Set[str]:
    permisos = set(getattr(current_user, "permisos_codes", []) or [])
    if permisos:
        return permisos

    for usuario_rol in getattr(current_user, "roles", []) or []:
        rol = getattr(usuario_rol, "rol", None)
        if not rol:
            continue
        for rol_permiso in getattr(rol, "permisos", []) or []:
            permiso = getattr(rol_permiso, "permiso", None)
            codigo = getattr(permiso, "codigo", None)
            if codigo:
                permisos.add(codigo)
    return permisos


def _es_admin(current_user: Usuario) -> bool:
    claves_rol: Set[str] = set()
    nombres_rol: Set[str] = set()

    for usuario_rol in getattr(current_user, "roles", []) or []:
        rol = getattr(usuario_rol, "rol", None)
        if not rol:
            continue
        if getattr(rol, "clave", None):
            claves_rol.add(str(rol.clave).strip().upper())
        if getattr(rol, "nombre", None):
            nombres_rol.add(str(rol.nombre).strip().lower())

    return (
        "ADMIN" in claves_rol
        or "ADMINISTRADOR" in claves_rol
        or "admin" in nombres_rol
        or "administrador" in nombres_rol
    )


def require_migration_access(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Valida acceso al modulo de migraciones (lectura y operaciones)."""
    permisos = _permisos_usuario(current_user)
    if (
        "sistema.admin" in permisos
        or "sistema.migraciones" in permisos
        or _es_admin(current_user)
    ):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tiene permisos para gestionar migraciones",
    )


def ejecutar_comando_alembic(comando: List[str]) -> tuple[bool, str]:
    """Ejecuta un comando de Alembic y retorna (success, output)."""
    comandos_a_probar: List[List[str]] = [comando]
    if comando and comando[0] == "alembic":
        alembic_local = Path(sys.executable).parent / (
            "alembic.exe" if sys.platform.startswith("win") else "alembic"
        )
        if alembic_local.exists():
            comandos_a_probar.append([str(alembic_local), *comando[1:]])

        candidatos_venv = [
            BASE_DIR / ".venv" / "Scripts" / "alembic.exe",
            BASE_DIR / "venv" / "Scripts" / "alembic.exe",
            BASE_DIR / ".venv" / "bin" / "alembic",
            BASE_DIR / "venv" / "bin" / "alembic",
        ]
        for candidato in candidatos_venv:
            if candidato.exists():
                comandos_a_probar.append([str(candidato), *comando[1:]])

    ultimo_error = "Error desconocido al ejecutar alembic"
    for cmd in comandos_a_probar:
        try:
            result = subprocess.run(
                cmd,
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = result.stdout + result.stderr
            if result.returncode == 0:
                return True, output
            ultimo_error = output or f"Comando fallido: {' '.join(cmd)}"
        except FileNotFoundError as exc:
            ultimo_error = f"Comando no encontrado ({' '.join(cmd)}): {exc}"
        except subprocess.TimeoutExpired:
            return False, "El comando excedio el tiempo limite de ejecucion"
        except Exception as exc:
            ultimo_error = f"Error al ejecutar {' '.join(cmd)}: {exc}"

    return False, ultimo_error


def obtener_revision_actual() -> Optional[str]:
    """Obtiene la revision actual reportada por Alembic."""
    success, output = ejecutar_comando_alembic(["alembic", "current"])
    if not success:
        return None

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"([a-zA-Z0-9]+)\b", line)
        if match:
            return match.group(1)

    return None


def _parse_down_revisions(raw_value: Optional[str]) -> List[str]:
    if not raw_value:
        return []

    value = raw_value.strip()
    try:
        parsed = ast.literal_eval(value)
    except Exception:
        parsed = value.strip('"\'')

    if parsed is None:
        return []

    if isinstance(parsed, (list, tuple, set)):
        return [str(item).strip() for item in parsed if item]

    normalized = str(parsed).strip()
    return [normalized] if normalized else []


def _leer_migraciones_desde_archivos() -> tuple[List[MigracionInfo], Dict[str, List[str]]]:
    """Lee archivos en alembic/versions y devuelve migraciones + mapa de padres."""
    versions_dir = BASE_DIR / "alembic" / "versions"
    if not versions_dir.exists():
        return [], {}

    migraciones: List[MigracionInfo] = []
    mapa_padres: Dict[str, List[str]] = {}

    for file_path in sorted(versions_dir.glob("*.py")):
        if file_path.name == "__init__.py":
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"Error al leer {file_path}: {exc}")
            continue

        revision_match = REVISION_RE.search(content)
        if not revision_match:
            continue
        revision = revision_match.group(1).strip()

        down_revision_match = DOWN_REVISION_RE.search(content)
        down_revision_raw = down_revision_match.group(1).strip() if down_revision_match else None
        down_revisions = _parse_down_revisions(down_revision_raw)
        down_revision = ",".join(down_revisions) if len(down_revisions) > 1 else (down_revisions[0] if down_revisions else None)

        descripcion = file_path.stem
        docstring_match = DOCSTRING_RE.search(content)
        if docstring_match:
            first_line = docstring_match.group(1).strip().splitlines()
            if first_line:
                descripcion = first_line[0].strip() or descripcion

        mapa_padres[revision] = down_revisions
        migraciones.append(
            MigracionInfo(
                revision=revision,
                down_revision=down_revision,
                descripcion=descripcion,
                fecha_creacion=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                aplicada=False,
                fecha_aplicacion=None,
            )
        )

    return migraciones, mapa_padres


def _calcular_revisiones_aplicadas(
    revision_actual: Optional[str],
    mapa_padres: Dict[str, List[str]],
) -> Set[str]:
    """Marca revision actual y sus ancestros como aplicados."""
    if not revision_actual:
        return set()

    aplicadas: Set[str] = set()
    pendientes: List[str] = [revision_actual]

    while pendientes:
        revision = pendientes.pop()
        if not revision or revision in aplicadas:
            continue
        aplicadas.add(revision)
        for parent in mapa_padres.get(revision, []):
            if parent and parent not in aplicadas:
                pendientes.append(parent)

    return aplicadas


def parsear_migraciones_desde_archivos() -> List[MigracionInfo]:
    """Construye la lista de migraciones y su estado aplicado."""
    migraciones, mapa_padres = _leer_migraciones_desde_archivos()
    revision_actual = obtener_revision_actual()
    revisiones_aplicadas = _calcular_revisiones_aplicadas(revision_actual, mapa_padres)

    for migracion in migraciones:
        migracion.aplicada = migracion.revision in revisiones_aplicadas

    return migraciones


def _construir_estado(
    migraciones: List[MigracionInfo],
    revision_actual: Optional[str],
) -> MigracionEstadoActual:
    total = len(migraciones)
    aplicadas = sum(1 for migracion in migraciones if migracion.aplicada)
    pendientes = total - aplicadas

    descripcion_actual = None
    if revision_actual:
        for migracion in migraciones:
            if migracion.revision == revision_actual:
                descripcion_actual = migracion.descripcion
                break

    return MigracionEstadoActual(
        revision_actual=revision_actual,
        descripcion=descripcion_actual,
        total_migraciones=total,
        migraciones_aplicadas=aplicadas,
        migraciones_pendientes=pendientes,
        ultima_actualizacion=datetime.now(),
    )


@router.get("/", response_model=MigracionListaResponse)
async def listar_migraciones(
    current_user: Usuario = Depends(require_migration_access),
):
    """Lista todas las migraciones disponibles y su estado."""
    try:
        migraciones = parsear_migraciones_desde_archivos()
        revision_actual = obtener_revision_actual()
        estado = _construir_estado(migraciones, revision_actual)
        return MigracionListaResponse(migraciones=migraciones, estado=estado)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener lista de migraciones: {exc}",
        )


@router.get("/current", response_model=MigracionEstadoActual)
async def obtener_estado_actual(
    current_user: Usuario = Depends(require_migration_access),
):
    """Obtiene el estado actual de las migraciones de la base de datos."""
    try:
        migraciones = parsear_migraciones_desde_archivos()
        revision_actual = obtener_revision_actual()
        return _construir_estado(migraciones, revision_actual)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado actual: {exc}",
        )


@router.get("/history")
async def obtener_historial(
    current_user: Usuario = Depends(require_migration_access),
):
    """Obtiene el historial de migraciones."""
    try:
        success, output = ejecutar_comando_alembic(["alembic", "history", "--verbose"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener historial de migraciones",
            )
        return {"historial": output, "timestamp": datetime.now()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial: {exc}",
        )


@router.post("/upgrade", response_model=MigracionOperacionResponse)
async def aplicar_migraciones(
    request: MigracionOperacionRequest,
    current_user: Usuario = Depends(require_migration_access),
):
    """Aplica migraciones hasta la revision especificada."""
    try:
        revision_anterior = obtener_revision_actual()
        success, output = ejecutar_comando_alembic(["alembic", "upgrade", request.target])

        if not success:
            return MigracionOperacionResponse(
                success=False,
                message="Error al aplicar migraciones",
                revision_anterior=revision_anterior,
                revision_nueva=None,
                output=output,
            )

        revision_nueva = obtener_revision_actual()
        return MigracionOperacionResponse(
            success=True,
            message=f"Migraciones aplicadas exitosamente hasta {request.target}",
            revision_anterior=revision_anterior,
            revision_nueva=revision_nueva,
            output=output,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al aplicar migraciones: {exc}",
        )


@router.post("/downgrade", response_model=MigracionOperacionResponse)
async def revertir_migraciones(
    request: MigracionOperacionRequest,
    current_user: Usuario = Depends(require_migration_access),
):
    """Revierte migraciones hasta la revision especificada."""
    try:
        revision_anterior = obtener_revision_actual()
        success, output = ejecutar_comando_alembic(["alembic", "downgrade", request.target])

        if not success:
            return MigracionOperacionResponse(
                success=False,
                message="Error al revertir migraciones",
                revision_anterior=revision_anterior,
                revision_nueva=None,
                output=output,
            )

        revision_nueva = obtener_revision_actual()
        return MigracionOperacionResponse(
            success=True,
            message=f"Migraciones revertidas exitosamente hasta {request.target}",
            revision_anterior=revision_anterior,
            revision_nueva=revision_nueva,
            output=output,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al revertir migraciones: {exc}",
        )
