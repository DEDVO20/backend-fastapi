"""
Cliente de Supabase para gestión de archivos
"""
import os
from typing import Optional, Tuple
from supabase import create_client, Client
from ..core.config import settings

# Inicializar cliente
supabase: Optional[Client] = None

if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def upload_file_bytes(file_content: bytes, file_name: str, content_type: str = "application/octet-stream", bucket: str = None) -> Tuple[bool, str]:
    """
    Sube un archivo (bytes) a Supabase Storage
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("❌ ERROR: Supabase no está configurado")
        return False, "Supabase no está configurado"
    
    target_bucket = bucket or settings.SUPABASE_BUCKET
    
    try:
        import requests
        
        # URL de la API de Supabase Storage
        upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{target_bucket}/{file_name}"
        
        # Headers para la petición
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": content_type,
            "x-upsert": "true"
        }
        
        response = requests.post(
            upload_url,
            data=file_content,
            headers=headers
        )
        
        if response.status_code not in [200, 201]:
            return False, f"Error subiendo a Supabase: {response.text}"
        
        # Construir URL pública
        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{target_bucket}/{file_name}"
        return True, public_url
        
    except Exception as e:
        print(f"❌ ERROR subiendo archivo: {str(e)}")
        return False, str(e)

def upload_avatar(file_path: str, file_name: str) -> Tuple[bool, str]:
    """
    Sube un avatar desde path local (Legacy wrapper)
    """
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        return upload_file_bytes(file_data, file_name, "image/webp", bucket="avatars") # Forzar bucket avatars para legacy path
    except Exception as e:
        return False, str(e)

def delete_file(file_name: str, bucket: str = None) -> Tuple[bool, str]:
    """
    Elimina un archivo de Supabase Storage
    """
    if not supabase:
        return False, "Supabase no está configurado"
    
    target_bucket = bucket or settings.SUPABASE_BUCKET
    try:
        supabase.storage.from_(target_bucket).remove([file_name])
        return True, "Archivo eliminado correctamente"
    except Exception as e:
        return False, str(e)

# Alias para compatibilidad
delete_avatar = delete_file

def get_file_name_from_url(url: str) -> Optional[str]:
    """
    Extrae la ruta del archivo de una URL de Supabase
    """
    if not url: return None
    try:
        parts = url.split('/')
        if 'public' in parts:
            public_idx = parts.index('public')
            if len(parts) > public_idx + 2:
                return '/'.join(parts[public_idx + 2:])
        return None
    except:
        return None

