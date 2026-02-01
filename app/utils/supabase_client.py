"""
Cliente de Supabase para gestión de archivos
"""
import os
from typing import Optional, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "avatars")

# Inicializar cliente
supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_avatar(file_path: str, file_name: str) -> Tuple[bool, str]:
    """
    Sube un avatar a Supabase Storage usando la API REST directamente
    
    Args:
        file_path: Ruta del archivo a subir
        file_name: Ruta del archivo en el bucket (puede incluir carpetas, ej: "usuario_id/avatar.webp")
        
    Returns:
        Tuple[bool, str]: (éxito, url_o_mensaje_error)
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ ERROR: Supabase no está configurado")
        return False, "Supabase no está configurado"
    
    try:
        import requests
        
        print(f"📤 Subiendo imagen: {file_name} desde {file_path}")
        print(f"🪣 Bucket: {SUPABASE_BUCKET}")
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        print(f"📦 Tamaño del archivo: {len(file_data)} bytes")
        
        # URL de la API de Supabase Storage
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{file_name}"
        
        print(f"🌐 URL de subida: {upload_url}")
        
        # Headers para la petición
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "image/webp",
            "x-upsert": "true"  # Sobrescribir si existe
        }
        
        # Subir archivo usando POST
        print(f"⬆️ Subiendo a Supabase via REST API...")
        response = requests.post(
            upload_url,
            data=file_data,
            headers=headers
        )
        
        print(f"📊 Status code: {response.status_code}")
        print(f"📄 Respuesta: {response.text[:500]}")
        
        if response.status_code not in [200, 201]:
            error_msg = f"Error HTTP {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            return False, error_msg
        
        # Construir URL pública
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{file_name}"
        
        print(f"✅ Archivo subido exitosamente")
        print(f"🔗 URL pública: {public_url}")
        
        # Verificar que el archivo existe
        verify_response = requests.head(public_url)
        print(f"🔍 Verificación (HEAD): {verify_response.status_code}")
        
        return True, public_url
        
    except Exception as e:
        print(f"❌ ERROR subiendo imagen: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def delete_avatar(file_name: str) -> Tuple[bool, str]:
    """
    Elimina un avatar de Supabase Storage
    
    Args:
        file_name: Nombre del archivo a eliminar
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    if not supabase:
        return False, "Supabase no está configurado"
    
    try:
        supabase.storage.from_(SUPABASE_BUCKET).remove([file_name])
        return True, "Archivo eliminado correctamente"
        
    except Exception as e:
        return False, str(e)


def get_file_name_from_url(url: str) -> Optional[str]:
    """
    Extrae la ruta del archivo de una URL de Supabase
    
    Args:
        url: URL completa del archivo
        
    Returns:
        Ruta del archivo (ej: "usuario_id/avatar.webp") o None
    """
    if not url:
        return None
    
    try:
        # URL format: https://project.supabase.co/storage/v1/object/public/bucket/path/to/file
        # Necesitamos extraer todo después del nombre del bucket
        parts = url.split('/')
        
        # Buscar el índice del bucket en la URL
        if 'public' in parts:
            public_idx = parts.index('public')
            # Todo después de 'public/bucket_name/' es la ruta del archivo
            if len(parts) > public_idx + 2:
                # Unir todas las partes después del bucket
                file_path = '/'.join(parts[public_idx + 2:])
                return file_path
        
        return None
    except:
        return None
