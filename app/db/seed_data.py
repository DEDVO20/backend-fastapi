"""
Script para crear datos iniciales en la base de datos
"""
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.usuario import Area, Usuario, UsuarioRol

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
    """Sincroniza el catálogo RBAC SGC-IUDC 2026 (roles, permisos y migraciones)."""
    from app.db.sync_rbac import sincronizar_rbac_sgc

    resultado = sincronizar_rbac_sgc(db)
    print("✅ Roles y permisos SGC-IUDC 2026 sincronizados")
    if resultado["roles_creados"]:
        print(f"   Creados: {', '.join(resultado['roles_creados'])}")
    if resultado["roles_eliminados"]:
        print(f"   Eliminados: {', '.join(resultado['roles_eliminados'])}")
    if resultado["usuarios_migrados"]:
        print(f"   Usuarios migrados: {resultado['usuarios_migrados']}")
    return resultado["roles"]


def crear_usuario_admin(db: Session, roles: dict):
    """Crear usuario administrador por defecto"""
    admin = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
    if admin:
        print("ℹ️  Usuario admin ya existe, verificando roles...")
    else:
        area_dir = db.query(Area).filter(Area.codigo == "DIR").first()
        admin = Usuario(
            documento=0,
            nombre="Administrador",
            primer_apellido="Sistema",
            correo_electronico="admin@sistema.com",
            nombre_usuario="admin",
            contrasena_hash=pwd_context.hash("admin123"),
            area_id=area_dir.id if area_dir else None,
            activo=True
        )
        db.add(admin)
        db.flush()
        print("✅ Usuario administrador creado")
    
    rol_admin = roles.get("admin")
    if rol_admin:
        ya_asignado = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == admin.id,
            UsuarioRol.rol_id == rol_admin.id,
        ).first()
        if not ya_asignado:
            db.add(UsuarioRol(usuario_id=admin.id, rol_id=rol_admin.id))
    
    db.commit()
    print("✅ Usuario administrador listo (usuario: admin, contraseña: admin123)")


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
