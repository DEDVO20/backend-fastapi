"""
Sincroniza el catálogo de permisos y roles SGC-IUDC 2026.

Reemplaza el listado histórico de códigos duplicados (roles.administrar,
documentos.editar, indicadores.ver, etc.) por la matriz canónica.
"""
from app.database import SessionLocal
from app.db.sync_rbac import sincronizar_rbac_sgc


def migrar_permisos():
    db = SessionLocal()
    print("🚀 Sincronizando catálogo RBAC SGC-IUDC 2026...")
    try:
        resultado = sincronizar_rbac_sgc(db)
        print("\n✅ Sincronización completada")
        print(f"  - Permisos creados: {len(resultado['permisos_creados'])}")
        print(f"  - Permisos eliminados: {resultado['permisos_eliminados']}")
        print(f"  - Roles creados: {resultado['roles_creados']}")
        print(f"  - Roles actualizados: {resultado['roles_actualizados']}")
        print(f"  - Roles eliminados: {resultado['roles_eliminados']}")
        print(f"  - Usuarios migrados: {resultado['usuarios_migrados']}")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error durante la migración: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrar_permisos()
