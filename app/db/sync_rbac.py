"""
Sincroniza roles y permisos con el catálogo SGC-IUDC 2026.

- Crea/actualiza permisos canónicos
- Reemplaza la matriz de cada rol canónico
- Migra usuarios de roles obsoletos
- Elimina roles y permisos que ya no aplican
"""
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.db.rbac_catalog import (
    CLAVES_ROLES_CANONICOS,
    MIGRACION_ROLES,
    PERMISOS,
    PERMISOS_OBSOLETOS,
    ROLES,
)
from app.models.usuario import Permiso, Rol, RolPermiso, UsuarioRol


def _resultado_vacio() -> Dict[str, Any]:
    return {
        "permisos_creados": [],
        "permisos_actualizados": [],
        "permisos_eliminados": [],
        "roles_creados": [],
        "roles_actualizados": [],
        "roles_eliminados": [],
        "usuarios_migrados": 0,
        "roles": {},
    }


def _upsert_permisos(db: Session, resultado: Dict[str, Any]) -> Dict[str, Permiso]:
    permisos: Dict[str, Permiso] = {}
    for data in PERMISOS:
        permiso = db.query(Permiso).filter(Permiso.codigo == data["codigo"]).first()
        if not permiso:
            permiso = Permiso(
                codigo=data["codigo"],
                nombre=data["nombre"],
                descripcion=data["descripcion"],
                activo=True,
            )
            db.add(permiso)
            db.flush()
            resultado["permisos_creados"].append(data["codigo"])
        else:
            permiso.nombre = data["nombre"]
            permiso.descripcion = data["descripcion"]
            permiso.activo = True
            resultado["permisos_actualizados"].append(data["codigo"])
        permisos[data["codigo"]] = permiso
    db.flush()
    return permisos


def _reemplazar_permisos_rol(db: Session, rol: Rol, codigos: List[str], permisos: Dict[str, Permiso]) -> None:
    db.query(RolPermiso).filter(RolPermiso.rol_id == rol.id).delete(synchronize_session=False)
    db.flush()
    vistos = set()
    for codigo in codigos:
        if codigo in vistos or codigo not in permisos:
            continue
        vistos.add(codigo)
        db.add(RolPermiso(rol_id=rol.id, permiso_id=permisos[codigo].id))
    db.flush()


def _upsert_roles(db: Session, permisos: Dict[str, Permiso], resultado: Dict[str, Any]) -> Dict[str, Rol]:
    roles: Dict[str, Rol] = {}
    for data in ROLES:
        rol = db.query(Rol).filter(Rol.clave == data["clave"]).first()
        if not rol:
            rol = Rol(
                nombre=data["nombre"],
                clave=data["clave"],
                descripcion=data["descripcion"],
                activo=True,
            )
            db.add(rol)
            db.flush()
            resultado["roles_creados"].append(data["clave"])
        else:
            rol.nombre = data["nombre"]
            rol.descripcion = data["descripcion"]
            rol.activo = True
            resultado["roles_actualizados"].append(data["clave"])
        _reemplazar_permisos_rol(db, rol, data["permisos"], permisos)
        roles[data["clave"]] = rol
    return roles


def _migrar_usuarios(db: Session, origen: Rol, destino: Rol) -> int:
    if origen.id == destino.id:
        return 0

    asignaciones = db.query(UsuarioRol).filter(UsuarioRol.rol_id == origen.id).all()
    destino_ids = {
        ur.usuario_id
        for ur in db.query(UsuarioRol).filter(UsuarioRol.rol_id == destino.id).all()
    }
    migrados = 0
    for asignacion in asignaciones:
        if asignacion.usuario_id in destino_ids:
            db.delete(asignacion)
        else:
            asignacion.rol_id = destino.id
            destino_ids.add(asignacion.usuario_id)
        migrados += 1
    db.flush()
    return migrados


def _eliminar_rol(db: Session, rol: Rol) -> None:
    db.query(RolPermiso).filter(RolPermiso.rol_id == rol.id).delete(synchronize_session=False)
    db.query(UsuarioRol).filter(UsuarioRol.rol_id == rol.id).delete(synchronize_session=False)
    db.flush()
    db.delete(rol)
    db.flush()


def _migrar_y_eliminar_obsoletos(db: Session, roles: Dict[str, Rol], resultado: Dict[str, Any]) -> None:
    claves_canonicas = set(CLAVES_ROLES_CANONICOS)
    for rol in db.query(Rol).all():
        clave = (rol.clave or "").strip().lower()
        destino_clave = MIGRACION_ROLES.get(clave)
        if not destino_clave or clave in claves_canonicas:
            continue
        destino = roles.get(destino_clave)
        if destino:
            resultado["usuarios_migrados"] += _migrar_usuarios(db, rol, destino)
        _eliminar_rol(db, rol)
        resultado["roles_eliminados"].append(rol.clave)


def _eliminar_permisos_obsoletos(db: Session, resultado: Dict[str, Any]) -> None:
    canonicos = {p["codigo"] for p in PERMISOS}
    huérfanos = db.query(Permiso).filter(Permiso.codigo.in_(PERMISOS_OBSOLETOS)).all()
    for permiso in huérfanos:
        if permiso.codigo in canonicos:
            continue
        db.query(RolPermiso).filter(RolPermiso.permiso_id == permiso.id).delete(
            synchronize_session=False
        )
        db.delete(permiso)
        resultado["permisos_eliminados"].append(permiso.codigo)
    db.flush()


def sincronizar_rbac_sgc(db: Session) -> Dict[str, Any]:
    """Aplica el catálogo SGC y deja la matriz alineada con privilegio mínimo."""
    resultado = _resultado_vacio()
    permisos = _upsert_permisos(db, resultado)
    roles = _upsert_roles(db, permisos, resultado)
    _migrar_y_eliminar_obsoletos(db, roles, resultado)
    _eliminar_permisos_obsoletos(db, resultado)
    db.commit()

    # Recargar roles canónicos tras el commit
    roles_finales = {
        clave: db.query(Rol).filter(Rol.clave == clave).first()
        for clave in CLAVES_ROLES_CANONICOS
    }
    resultado["roles"] = {k: v for k, v in roles_finales.items() if v}
    return resultado


if __name__ == "__main__":
    from app.database import SessionLocal

    session = SessionLocal()
    try:
        resumen = sincronizar_rbac_sgc(session)
        print("✅ RBAC SGC-IUDC 2026 sincronizado")
        print(f"  Roles creados: {resumen['roles_creados']}")
        print(f"  Roles actualizados: {resumen['roles_actualizados']}")
        print(f"  Roles eliminados: {resumen['roles_eliminados']}")
        print(f"  Usuarios migrados: {resumen['usuarios_migrados']}")
        print(f"  Permisos creados: {resumen['permisos_creados']}")
        print(f"  Permisos eliminados: {resumen['permisos_eliminados']}")
    except Exception as exc:
        session.rollback()
        print(f"❌ Error sincronizando RBAC: {exc}")
        raise
    finally:
        session.close()
