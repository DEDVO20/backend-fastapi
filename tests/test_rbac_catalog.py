"""Pruebas del catálogo RBAC SGC-IUDC 2026."""
from app.db.rbac_catalog import (
    CLAVES_ROLES_CANONICOS,
    CODIGOS_PERMISOS,
    MIGRACION_ROLES,
    PERMISOS_OBSOLETOS,
    ROLES,
    rol_por_clave,
)


def test_roles_canonicos_son_los_cinco_de_la_documentacion():
    assert CLAVES_ROLES_CANONICOS == [
        "admin",
        "lider_proceso",
        "auditor",
        "colaborador",
        "invitado",
    ]


def test_admin_tiene_acceso_total():
    admin = rol_por_clave("admin")
    assert "sistema.admin" in admin["permisos"]
    assert "usuarios.gestion" in admin["permisos"]
    assert "auditorias.planificar" in admin["permisos"]
    assert set(admin["permisos"]) == set(CODIGOS_PERMISOS)


def test_lider_proceso_no_eleva_privilegios_ni_ve_logs():
    lider = rol_por_clave("lider_proceso")
    prohibidos = {
        "sistema.admin",
        "sistema.config",
        "usuarios.gestion",
        "usuarios.crear",
        "documentos.anular",
        "auditorias.planificar",
        "noconformidades.cerrar",
    }
    assert not prohibidos.intersection(lider["permisos"])
    assert "documentos.aprobar" in lider["permisos"]
    assert "noconformidades.gestion" in lider["permisos"]
    assert "riesgos.gestion" in lider["permisos"]
    assert "usuarios.ver" in lider["permisos"]


def test_auditor_consulta_y_ejecuta_sin_modificar_maestro():
    auditor = rol_por_clave("auditor")
    assert "auditorias.ejecutar" in auditor["permisos"]
    assert "auditorias.ver" in auditor["permisos"]
    assert "documentos.ver" in auditor["permisos"]
    assert "procesos.ver" in auditor["permisos"]
    assert "procesos.admin" not in auditor["permisos"]
    assert "documentos.aprobar" not in auditor["permisos"]
    assert "auditorias.planificar" not in auditor["permisos"]
    assert "usuarios.gestion" not in auditor["permisos"]


def test_colaborador_consulta_y_carga_evidencias():
    colaborador = rol_por_clave("colaborador")
    assert "documentos.ver" in colaborador["permisos"]
    assert "documentos.crear" in colaborador["permisos"]
    assert "noconformidades.reportar" in colaborador["permisos"]
    assert "noconformidades.gestion" not in colaborador["permisos"]
    assert "usuarios.gestion" not in colaborador["permisos"]


def test_invitado_solo_mapa_publico():
    invitado = rol_por_clave("invitado")
    assert invitado["permisos"] == ["procesos.ver"]


def test_roles_obsoletos_se_migran():
    assert MIGRACION_ROLES["gestor_calidad"] == "admin"
    assert MIGRACION_ROLES["coordinador"] == "lider_proceso"
    assert MIGRACION_ROLES["auxiliar"] == "colaborador"
    assert MIGRACION_ROLES["lider_siso"] == "lider_proceso"


def test_permisos_duplicados_historicos_quedan_fuera_del_catalogo():
    canonicos = set(CODIGOS_PERMISOS)
    assert not canonicos.intersection(PERMISOS_OBSOLETOS)
    assert "roles.administrar" in PERMISOS_OBSOLETOS
    assert "tickets.soporte" in PERMISOS_OBSOLETOS


def test_todos_los_permisos_de_roles_existen_en_catalogo():
    canonicos = set(CODIGOS_PERMISOS)
    for rol in ROLES:
        desconocidos = set(rol["permisos"]) - canonicos
        assert not desconocidos, f"{rol['clave']}: {desconocidos}"
