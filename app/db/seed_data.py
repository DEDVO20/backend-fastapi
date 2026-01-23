"""
Script para crear datos iniciales en la base de datos
"""
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.usuario import Area, Usuario, Rol, Permiso, RolPermiso, UsuarioRol
from app.models import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def crear_areas_iniciales(db: Session):
    """Crear áreas iniciales"""
    areas_data = [
        {"codigo": "DIR", "nombre": "Dirección", "descripcion": "Dirección General"},
        {"codigo": "ADM", "nombre": "Administración", "descripcion": "Área Administrativa"},
        {"codigo": "OPE", "nombre": "Operaciones", "descripcion": "Área de Operaciones"},
        {"codigo": "CAL", "nombre": "Calidad", "descripcion": "Gestión de Calidad"},
        {"codigo": "TEC", "nombre": "Tecnología", "descripcion": "Tecnología e Innovación"},
    ]
    
    for area_data in areas_data:
        area = db.query(Area).filter(Area.codigo == area_data["codigo"]).first()
        if not area:
            area = Area(**area_data)
            db.add(area)
    
    db.commit()
    print("✅ Áreas iniciales creadas")


def crear_roles_permisos_iniciales(db: Session):
    """Crear roles y permisos iniciales"""
    # Crear permisos básicos
    permisos_data = [
        {"nombre": "Ver Usuarios", "codigo": "usuarios.ver", "descripcion": "Permiso para ver usuarios"},
        {"nombre": "Crear Usuarios", "codigo": "usuarios.crear", "descripcion": "Permiso para crear usuarios"},
        {"nombre": "Editar Usuarios", "codigo": "usuarios.editar", "descripcion": "Permiso para editar usuarios"},
        {"nombre": "Eliminar Usuarios", "codigo": "usuarios.eliminar", "descripcion": "Permiso para eliminar usuarios"},
        {"nombre": "Administrar Sistema", "codigo": "sistema.admin", "descripcion": "Acceso completo al sistema"},
    ]
    
    permisos = {}
    for permiso_data in permisos_data:
        permiso = db.query(Permiso).filter(Permiso.codigo == permiso_data["codigo"]).first()
        if not permiso:
            permiso = Permiso(**permiso_data)
            db.add(permiso)
            db.flush()
        permisos[permiso_data["codigo"]] = permiso
    
    # Crear roles
    roles_data = [
        {
            "nombre": "Administrador del Sistema",
            "clave": "admin",
            "descripcion": "Acceso completo al sistema",
            "permisos": ["sistema.admin", "usuarios.ver", "usuarios.crear", "usuarios.editar", "usuarios.eliminar"]
        },
        {
            "nombre": "Gestor de Calidad",
            "clave": "gestor_calidad",
            "descripcion": "Gestión de procesos de calidad",
            "permisos": ["usuarios.ver"]
        },
        {
            "nombre": "Auditor",
            "clave": "auditor",
            "descripcion": "Realización de auditorías",
            "permisos": ["usuarios.ver"]
        },
        {
            "nombre": "Usuario Básico",
            "clave": "usuario",
            "descripcion": "Usuario del sistema con acceso básico",
            "permisos": ["usuarios.ver"]
        },
    ]
    
    roles = {}
    for rol_data in roles_data:
        permisos_rol = rol_data.pop("permisos")
        rol = db.query(Rol).filter(Rol.clave == rol_data["clave"]).first()
        if not rol:
            rol = Rol(**rol_data)
            db.add(rol)
            db.flush()
            
            # Asignar permisos al rol
            for permiso_codigo in permisos_rol:
                if permiso_codigo in permisos:
                    rol_permiso = RolPermiso(rol_id=rol.id, permiso_id=permisos[permiso_codigo].id)
                    db.add(rol_permiso)
        
        roles[rol_data["clave"]] = rol
    
    db.commit()
    print("✅ Roles y permisos iniciales creados")
    return roles


def crear_usuario_admin(db: Session, roles: dict):
    """Crear usuario administrador por defecto"""
    # Verificar si ya existe
    admin = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
    if admin:
        print("ℹ️  Usuario admin ya existe")
        return
    
    # Obtener área de dirección
    area_dir = db.query(Area).filter(Area.codigo == "DIR").first()
    
    # Crear usuario admin
    admin = Usuario(
        documento=0,
        nombre="Administrador",
        primer_apellido="Sistema",
        correo_electronico="admin@sistema.com",
        nombre_usuario="admin",
        contrasena_hash=pwd_context.hash("admin123"),  # Cambiar en producción
        area_id=area_dir.id if area_dir else None,
        activo=True
    )
    db.add(admin)
    db.flush()
    
    # Asignar rol de administrador
    if "admin" in roles:
        usuario_rol = UsuarioRol(usuario_id=admin.id, rol_id=roles["admin"].id)
        db.add(usuario_rol)
    
    db.commit()
    print("✅ Usuario administrador creado (usuario: admin, contraseña: admin123)")


def init_data(db: Session):
    """Inicializar todos los datos"""
    print("🌱 Insertando datos iniciales...")
    
    crear_areas_iniciales(db)
    roles = crear_roles_permisos_iniciales(db)
    crear_usuario_admin(db, roles)
    
    print("✅ Datos iniciales insertados correctamente!")


if __name__ == "__main__":
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        init_data(db)
    finally:
        db.close()
