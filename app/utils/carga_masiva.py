"""
Utilidades para carga masiva de usuarios desde Excel/CSV
"""
import io
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session, joinedload

from ..models.usuario import Area, Usuario, Rol, UsuarioRol
from ..schemas.usuario import CargaMasivaErrorDetalle
from ..utils.security import get_password_hash


COLUMNAS_REQUERIDAS = [
    'documento',
    'nombre',
    'primer_apellido',
    'correo_electronico',
    'nombre_usuario',
    'contrasena',
    'area_codigo',
    'roles',
]

COLUMNAS_PLANTILLA = [
    'documento',
    'nombre',
    'segundo_nombre',
    'primer_apellido',
    'segundo_apellido',
    'correo_electronico',
    'nombre_usuario',
    'contrasena',
    'area_codigo',
    'roles',
    'activo',
]

ALIAS_COLUMNAS = {
    'document': 'documento',
    'cedula': 'documento',
    'identificacion': 'documento',
    'id': 'documento',
    'primer_nombre': 'nombre',
    'apellido': 'primer_apellido',
    'apellido_1': 'primer_apellido',
    'correo': 'correo_electronico',
    'email': 'correo_electronico',
    'e_mail': 'correo_electronico',
    'mail': 'correo_electronico',
    'usuario': 'nombre_usuario',
    'username': 'nombre_usuario',
    'user': 'nombre_usuario',
    'password': 'contrasena',
    'pass': 'contrasena',
    'clave': 'contrasena',
    'area': 'area_codigo',
    'codigo_area': 'area_codigo',
    'codigo_de_area': 'area_codigo',
    'area_code': 'area_codigo',
    'rol': 'roles',
    'role': 'roles',
    'estado': 'activo',
}

MIN_PASSWORD_LENGTH = 8


def _quitar_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize('NFKD', texto)
    return ''.join(ch for ch in normalizado if not unicodedata.combining(ch))


def normalizar_nombre_columna(nombre: Any) -> str:
    """Normaliza encabezados (espacios, tildes, BOM) al formato interno."""
    texto = str(nombre or '').replace('\ufeff', '').strip().lower()
    texto = _quitar_acentos(texto)
    texto = re.sub(r'[^a-z0-9]+', '_', texto).strip('_')
    return ALIAS_COLUMNAS.get(texto, texto)


def valor_texto(valor: Any, default: str = '') -> str:
    if valor is None:
        return default
    try:
        if pd.isna(valor):
            return default
    except (TypeError, ValueError):
        pass

    texto = str(valor).strip()
    if texto.lower() in {'', 'nan', 'none', 'null', 'nat'}:
        return default
    return texto


def parse_documento(valor: Any) -> Optional[int]:
    texto = valor_texto(valor).replace(' ', '').replace(',', '')
    if not texto:
        return None
    if re.fullmatch(r'\d+\.0+', texto):
        texto = texto.split('.', 1)[0]
    try:
        return int(float(texto))
    except (TypeError, ValueError):
        return None


def parse_activo(valor: Any, default: bool = True) -> bool:
    texto = valor_texto(valor).lower()
    if not texto:
        return default
    if texto in {'true', '1', 'si', 'sí', 'yes', 'y', 'activo'}:
        return True
    if texto in {'false', '0', 'no', 'n', 'inactivo'}:
        return False
    return default


def validar_archivo(file: UploadFile) -> Tuple[bool, str]:
    """Valida que el archivo sea del tipo correcto"""
    if not file.filename:
        return False, "El archivo no tiene nombre"

    extension = file.filename.split('.')[-1].lower()
    if extension not in ['xlsx', 'xls', 'csv']:
        return False, f"Tipo de archivo no soportado: .{extension}. Use .xlsx, .xls o .csv"

    return True, ""


def leer_archivo(file_content: bytes, filename: str) -> pd.DataFrame:
    """Lee Excel o CSV, normaliza encabezados y descarta filas vacías."""
    if not file_content:
        raise ValueError("El archivo está vacío")

    extension = filename.split('.')[-1].lower()

    if extension in ['xlsx', 'xls']:
        try:
            df = pd.read_excel(io.BytesIO(file_content), dtype=str)
        except Exception as exc:
            raise ValueError(
                "No se pudo leer el Excel. Guárdelo como .xlsx o .csv e inténtelo de nuevo."
            ) from exc
    else:
        df = None
        ultimo_error = None
        for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
            try:
                df = pd.read_csv(
                    io.BytesIO(file_content),
                    encoding=encoding,
                    sep=None,
                    engine='python',
                    dtype=str,
                )
                break
            except Exception as exc:
                ultimo_error = exc
        if df is None:
            raise ValueError(
                f"No se pudo leer el CSV. Verifique la codificación y el separador. Detalle: {ultimo_error}"
            )

    df.columns = [normalizar_nombre_columna(col) for col in df.columns]
    df = df.loc[:, ~pd.Index(df.columns).duplicated()]
    df = df.dropna(how='all')
    df = df[~df.apply(lambda fila: all(not valor_texto(v) for v in fila), axis=1)]
    df = df.reset_index(drop=True)
    return df


def validar_columnas(df: pd.DataFrame) -> List[str]:
    """Valida que el DataFrame tenga las columnas requeridas"""
    return [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]


def cargar_caches(db: Session) -> Tuple[Dict[str, Area], Dict[str, Rol]]:
    """Carga áreas y roles indexados por código/clave y por nombre."""
    areas = db.query(Area).all()
    roles = db.query(Rol).all()

    areas_cache: Dict[str, Area] = {}
    for area in areas:
        if area.codigo:
            areas_cache[area.codigo.strip().upper()] = area
        if area.nombre:
            areas_cache[normalizar_nombre_columna(area.nombre)] = area

    roles_cache: Dict[str, Rol] = {}
    for rol in roles:
        if rol.clave:
            roles_cache[rol.clave.strip().lower()] = rol
        if rol.nombre:
            roles_cache[normalizar_nombre_columna(rol.nombre)] = rol

    return areas_cache, roles_cache


def _resolver_area(codigo: str, areas_cache: Dict[str, Area]) -> Optional[Area]:
    if not codigo:
        return None
    return areas_cache.get(codigo.upper()) or areas_cache.get(normalizar_nombre_columna(codigo))


def _resolver_roles(roles_str: str, roles_cache: Dict[str, Rol]) -> Tuple[List[Any], List[str]]:
    claves = [r.strip() for r in re.split(r'[,;|]', roles_str) if r.strip()]
    encontrados = []
    invalidos = []
    vistos = set()
    for clave in claves:
        rol = roles_cache.get(clave.lower()) or roles_cache.get(normalizar_nombre_columna(clave))
        if not rol:
            invalidos.append(clave)
            continue
        if rol.id in vistos:
            continue
        vistos.add(rol.id)
        encontrados.append(rol)
    return encontrados, invalidos


def procesar_fila(
    fila_num: int,
    fila: pd.Series,
    db: Session,
    areas_cache: Dict[str, Area],
    roles_cache: Dict[str, Rol],
    documentos_en_archivo: Optional[set] = None,
    emails_en_archivo: Optional[set] = None,
    usernames_en_archivo: Optional[set] = None,
) -> Tuple[bool, Any]:
    """
    Procesa una fila del archivo
    Retorna: (exito, resultado)
    - Si exito=True, resultado es el usuario creado
    - Si exito=False, resultado es lista de errores
    """
    errores: List[CargaMasivaErrorDetalle] = []
    documentos_en_archivo = documentos_en_archivo if documentos_en_archivo is not None else set()
    emails_en_archivo = emails_en_archivo if emails_en_archivo is not None else set()
    usernames_en_archivo = usernames_en_archivo if usernames_en_archivo is not None else set()

    documento = parse_documento(fila.get('documento'))
    if documento is None:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='documento',
            valor=valor_texto(fila.get('documento')) or None,
            error='El documento es obligatorio y debe ser numérico',
        ))

    nombre = valor_texto(fila.get('nombre'))
    if not nombre:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='nombre',
            valor=valor_texto(fila.get('nombre')) or None,
            error='El nombre es obligatorio',
        ))

    primer_apellido = valor_texto(fila.get('primer_apellido'))
    if not primer_apellido:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='primer_apellido',
            valor=valor_texto(fila.get('primer_apellido')) or None,
            error='El primer apellido es obligatorio',
        ))

    email = valor_texto(fila.get('correo_electronico'))
    if not email:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='correo_electronico',
            valor=None,
            error='El correo electrónico es obligatorio',
        ))
    elif '@' not in email:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='correo_electronico',
            valor=email,
            error='El correo electrónico no es válido',
        ))

    username = valor_texto(fila.get('nombre_usuario'))
    if not username:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='nombre_usuario',
            valor=None,
            error='El nombre de usuario es obligatorio',
        ))

    contrasena = valor_texto(fila.get('contrasena'))
    if len(contrasena) < MIN_PASSWORD_LENGTH:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='contrasena',
            valor='***',
            error=f'La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres',
        ))

    if errores:
        return False, errores

    if documento in documentos_en_archivo:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='documento',
            valor=str(documento),
            error=f'El documento {documento} está duplicado en el archivo',
        ))
    elif db.query(Usuario).filter(Usuario.documento == documento).first():
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='documento',
            valor=str(documento),
            error=f'El documento {documento} ya existe en el sistema',
        ))

    if email.lower() in emails_en_archivo:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='correo_electronico',
            valor=email,
            error=f'El correo {email} está duplicado en el archivo',
        ))
    elif db.query(Usuario).filter(Usuario.correo_electronico == email).first():
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='correo_electronico',
            valor=email,
            error=f'El correo {email} ya existe en el sistema',
        ))

    if username.lower() in usernames_en_archivo:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='nombre_usuario',
            valor=username,
            error=f'El nombre de usuario {username} está duplicado en el archivo',
        ))
    elif db.query(Usuario).filter(Usuario.nombre_usuario == username).first():
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='nombre_usuario',
            valor=username,
            error=f'El nombre de usuario {username} ya existe en el sistema',
        ))

    area_codigo = valor_texto(fila.get('area_codigo'))
    area = _resolver_area(area_codigo, areas_cache)
    if not area_codigo:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='area_codigo',
            valor=area_codigo,
            error='El código de área es obligatorio',
        ))
    elif not area:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='area_codigo',
            valor=area_codigo,
            error=f'El área con código {area_codigo} no existe',
        ))

    roles_str = valor_texto(fila.get('roles'))
    roles_encontrados, roles_invalidos = _resolver_roles(roles_str, roles_cache)
    if not roles_str:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='roles',
            valor=roles_str,
            error='Debe especificar al menos un rol',
        ))
    elif roles_invalidos:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='roles',
            valor=', '.join(roles_invalidos),
            error=f'Roles no encontrados: {", ".join(roles_invalidos)}',
        ))

    if errores:
        return False, errores

    segundo_nombre = valor_texto(fila.get('segundo_nombre')) or None
    segundo_apellido = valor_texto(fila.get('segundo_apellido')) or None

    try:
        with db.begin_nested():
            nuevo_usuario = Usuario(
                documento=documento,
                nombre=nombre,
                segundo_nombre=segundo_nombre,
                primer_apellido=primer_apellido,
                segundo_apellido=segundo_apellido,
                correo_electronico=email,
                nombre_usuario=username,
                contrasena_hash=get_password_hash(contrasena),
                area_id=area.id,
                activo=parse_activo(fila.get('activo'), True),
            )
            db.add(nuevo_usuario)
            db.flush()
            for rol in roles_encontrados:
                db.add(UsuarioRol(usuario_id=nuevo_usuario.id, rol_id=rol.id))
            db.flush()

        documentos_en_archivo.add(documento)
        emails_en_archivo.add(email.lower())
        usernames_en_archivo.add(username.lower())
        return True, nuevo_usuario

    except Exception as e:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='general',
            valor=None,
            error=f'Error al crear usuario: {str(e)}',
        ))
        return False, errores


def _excel_bytes(hojas: Dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for nombre, df in hojas.items():
            df.to_excel(writer, sheet_name=nombre[:31], index=False)
    return output.getvalue()


def generar_plantilla_excel(areas: List[Area], roles: List[Rol]) -> bytes:
    """Genera una plantilla .xlsx con ejemplos reales de áreas y roles."""
    area_ejemplo = areas[0].codigo if areas else 'CAL'
    rol_ejemplo = next((r.clave for r in roles if r.clave != 'admin'), None)
    if not rol_ejemplo:
        rol_ejemplo = roles[0].clave if roles else 'auxiliar'
    rol_admin = next((r.clave for r in roles if r.clave == 'admin'), rol_ejemplo)

    ejemplos = pd.DataFrame([
        {
            'documento': '10000001',
            'nombre': 'Juan',
            'segundo_nombre': 'Carlos',
            'primer_apellido': 'Perez',
            'segundo_apellido': 'Garcia',
            'correo_electronico': 'juan.perez@empresa.com',
            'nombre_usuario': 'jperez',
            'contrasena': 'Password123',
            'area_codigo': area_ejemplo,
            'roles': rol_ejemplo,
            'activo': 'true',
        },
        {
            'documento': '10000002',
            'nombre': 'Maria',
            'segundo_nombre': 'Elena',
            'primer_apellido': 'Lopez',
            'segundo_apellido': 'Martinez',
            'correo_electronico': 'maria.lopez@empresa.com',
            'nombre_usuario': 'mlopez',
            'contrasena': 'Password123',
            'area_codigo': area_ejemplo,
            'roles': f'{rol_ejemplo},{rol_admin}' if rol_admin != rol_ejemplo else rol_ejemplo,
            'activo': 'true',
        },
    ])

    df_areas = pd.DataFrame(
        [{'codigo': a.codigo, 'nombre': a.nombre} for a in areas]
        or [{'codigo': '', 'nombre': 'No hay áreas registradas'}]
    )
    df_roles = pd.DataFrame(
        [{'clave': r.clave, 'nombre': r.nombre, 'descripcion': r.descripcion or ''} for r in roles]
        or [{'clave': '', 'nombre': 'No hay roles registrados', 'descripcion': ''}]
    )

    instrucciones = pd.DataFrame([
        {'campo': 'documento', 'obligatorio': 'Sí', 'indicacion': 'Solo números. Debe ser único.'},
        {'campo': 'nombre', 'obligatorio': 'Sí', 'indicacion': 'Primer nombre del usuario.'},
        {'campo': 'segundo_nombre', 'obligatorio': 'No', 'indicacion': 'Dejar vacío si no aplica.'},
        {'campo': 'primer_apellido', 'obligatorio': 'Sí', 'indicacion': 'Primer apellido.'},
        {'campo': 'segundo_apellido', 'obligatorio': 'No', 'indicacion': 'Dejar vacío si no aplica.'},
        {'campo': 'correo_electronico', 'obligatorio': 'Sí', 'indicacion': 'Correo válido y único.'},
        {'campo': 'nombre_usuario', 'obligatorio': 'Sí', 'indicacion': 'Usuario de acceso, único.'},
        {'campo': 'contrasena', 'obligatorio': 'Sí', 'indicacion': f'Mínimo {MIN_PASSWORD_LENGTH} caracteres.'},
        {'campo': 'area_codigo', 'obligatorio': 'Sí', 'indicacion': 'Use un código de la hoja Areas.'},
        {'campo': 'roles', 'obligatorio': 'Sí', 'indicacion': 'Claves de la hoja Roles, separadas por coma.'},
        {'campo': 'activo', 'obligatorio': 'No', 'indicacion': 'true/false. Por defecto true.'},
    ])

    return _excel_bytes({
        'Usuarios': ejemplos,
        'Instrucciones': instrucciones,
        'Areas': df_areas,
        'Roles': df_roles,
    })


def generar_exportacion_usuarios(db: Session) -> bytes:
    """Exporta los usuarios actuales a Excel (sin contraseñas)."""
    usuarios = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.area),
            joinedload(Usuario.roles).joinedload(UsuarioRol.rol),
        )
        .order_by(Usuario.nombre_usuario)
        .all()
    )

    filas = []
    for usuario in usuarios:
        roles = []
        for asignacion in usuario.roles or []:
            if asignacion.rol and asignacion.rol.clave:
                roles.append(asignacion.rol.clave)
        filas.append({
            'documento': usuario.documento,
            'nombre': usuario.nombre or '',
            'segundo_nombre': usuario.segundo_nombre or '',
            'primer_apellido': usuario.primer_apellido or '',
            'segundo_apellido': usuario.segundo_apellido or '',
            'correo_electronico': usuario.correo_electronico or '',
            'nombre_usuario': usuario.nombre_usuario or '',
            'contrasena': '',
            'area_codigo': usuario.area.codigo if usuario.area else '',
            'roles': ','.join(roles),
            'activo': 'true' if usuario.activo else 'false',
        })

    df_usuarios = pd.DataFrame(filas, columns=COLUMNAS_PLANTILLA)
    nota = pd.DataFrame([
        {
            'nota': (
                'Las contraseñas no se exportan porque están cifradas. '
                'Este archivo es de consulta. Para crear usuarios nuevos use la plantilla '
                'e incluya una contraseña de al menos 8 caracteres.'
            )
        }
    ])
    return _excel_bytes({
        'Usuarios': df_usuarios,
        'Nota': nota,
    })
