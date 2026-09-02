from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from typing import Optional
import uuid
import mimetypes
from ..utils.supabase_client import upload_file_bytes
from .dependencies import require_any_permission
from ..models.usuario import Usuario

router = APIRouter(
    prefix="/api/v1/uploads",
    tags=["Uploads"],
    responses={404: {"description": "Not found"}},
)

ACCESO_USUARIO_AUTENTICADO_PERMISSIONS = [
    "sistema.admin",
    "calidad.ver",
    "documentos.crear",
    "documentos.ver",
    "documentos.revisar",
    "auditorias.ver",
    "capacitaciones.gestion",
    "noconformidades.reportar",
    "noconformidades.gestion",
    "usuarios.ver",
    "usuarios.gestion",
]

@router.post("/evidencia", response_model=dict)
async def upload_evidencia(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(require_any_permission(ACCESO_USUARIO_AUTENTICADO_PERMISSIONS))
):
    """
    Sube un archivo de evidencia (pdf, imagen, doc) y devuelve la URL pública.
    """
    mime = (file.content_type or "").split(";")[0].strip().lower()
    extension = ""
    if file.filename and "." in file.filename:
        extension = "." + file.filename.rsplit(".", 1)[-1].lower()

    allowed_types = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "text/csv",
        "text/plain",
        "application/csv",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    }
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".gif", ".csv", ".txt", ".doc", ".docx", ".xls", ".xlsx"}

    if mime and mime not in allowed_types and extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido. Usa PDF, imagen, Word, Excel o CSV.",
        )

    try:
        content = await file.read()

        file_ext = extension or mimetypes.guess_extension(mime) or ""
        filename = f"evidencias/{uuid.uuid4()}{file_ext}"

        success, result = upload_file_bytes(
            content,
            filename,
            mime or "application/octet-stream",
            bucket="documentos",
        )

        if not success:
            raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {result}")

        return {"url": result, "filename": file.filename}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logo", response_model=dict)
async def upload_logo(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(require_any_permission(["sistema.admin", "sistema.config"]))
):
    """
    Sube el logo del sistema (solo admin).
    """
    # Verificar permisos por codigo (no por nombre visible)
    permisos_usuario = set()
    try:
        permisos_usuario = set(getattr(current_user, "permisos_codes", []) or [])
    except Exception:
        permisos_usuario = set()

    if not permisos_usuario:
        for usuario_rol in getattr(current_user, "roles", []) or []:
            rol = getattr(usuario_rol, "rol", None)
            if not rol:
                continue
            for rol_permiso in getattr(rol, "permisos", []) or []:
                permiso = getattr(rol_permiso, "permiso", None)
                codigo = getattr(permiso, "codigo", None)
                if codigo:
                    permisos_usuario.add(str(codigo))
    
    # Lista de permisos que permiten subir el logo del sistema
    permisos_permitidos = [
        "sistema.admin",           # Administrador del sistema
        "sistema.configurar",      # Configuración del sistema
        "sistema.config",          # Alias de configuración
    ]
    
    if not any(permiso in permisos_usuario for permiso in permisos_permitidos):
        raise HTTPException(
            status_code=403, 
            detail=f"No tienes permisos para realizar esta acción. Permisos requeridos: {', '.join(permisos_permitidos)}"
        )

    # Validar que sea imagen
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    try:
        content = await file.read()
        
        # Nombre fijo o dinámico? Mejor único para evitar cache agresivo
        file_ext = mimetypes.guess_extension(file.content_type) or ""
        if not file_ext and file.filename:
            file_ext = "." + file.filename.split(".")[-1]
            
        filename = f"system/logo_{uuid.uuid4()}{file_ext}"
        
        # Subir al bucket "imagenes"
        success, result = upload_file_bytes(content, filename, file.content_type, bucket="imagenes")
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Error subiendo logo: {result}")
            
        return {"url": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
