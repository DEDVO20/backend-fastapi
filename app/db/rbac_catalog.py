"""
Catálogo RBAC del SGC-IUDC 2026 (ISO 9001 / 27001).

Fuente de verdad de roles y permisos. El seed y la sincronización
reemplazan la matriz operativa con estos perfiles jerárquicos.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# Permisos granulares (Lectura, Escritura, Aprobación, Administración)
# ---------------------------------------------------------------------------

PERMISOS: List[Dict[str, str]] = [
    # Identidades y gobernanza (Módulo VII)
    {
        "codigo": "sistema.admin",
        "nombre": "Administración total del SGC",
        "descripcion": "Acceso completo de gobernanza. Bypass de la matriz RBAC.",
    },
    {
        "codigo": "sistema.config",
        "nombre": "Configuración global del SGC",
        "descripcion": "Variables de entorno, sedes, organigrama y parametrización.",
    },
    {
        "codigo": "usuarios.ver",
        "nombre": "Ver usuarios",
        "descripcion": "Consulta de identidades (equipo / directorio).",
    },
    {
        "codigo": "usuarios.crear",
        "nombre": "Crear usuarios",
        "descripcion": "Alta de cuentas institucionales.",
    },
    {
        "codigo": "usuarios.editar",
        "nombre": "Editar usuarios",
        "descripcion": "Activación, desactivación y actualización de perfiles.",
    },
    {
        "codigo": "usuarios.eliminar",
        "nombre": "Eliminar usuarios",
        "descripcion": "Baja de cuentas del directorio.",
    },
    {
        "codigo": "usuarios.gestion",
        "nombre": "Gestión de identidades y roles",
        "descripcion": "Matriz de permisos, asignación de roles y gobernanza RBAC.",
    },
    {
        "codigo": "areas.gestionar",
        "nombre": "Gestionar estructura organizacional",
        "descripcion": "Áreas, facultades y responsables del organigrama.",
    },
    # Gestión documental
    {
        "codigo": "documentos.ver",
        "nombre": "Ver documentos",
        "descripcion": "Consulta y descarga de información documentada.",
    },
    {
        "codigo": "documentos.crear",
        "nombre": "Crear / cargar documentos",
        "descripcion": "Borradores, evidencias y solicitudes de cambio.",
    },
    {
        "codigo": "documentos.revisar",
        "nombre": "Revisar documentos",
        "descripcion": "Revisión técnica y solicitud de cambios del área.",
    },
    {
        "codigo": "documentos.aprobar",
        "nombre": "Aprobar documentos",
        "descripcion": "Aprobación y publicación del documento maestro.",
    },
    {
        "codigo": "documentos.anular",
        "nombre": "Anular documentos",
        "descripcion": "Obsolescencia y retiro del documento maestro.",
    },
    # Procesos
    {
        "codigo": "procesos.ver",
        "nombre": "Ver mapa y fichas de proceso",
        "descripcion": "Consulta del mapa de procesos y caracterizaciones.",
    },
    {
        "codigo": "procesos.admin",
        "nombre": "Administrar procesos",
        "descripcion": "Crear, editar y cerrar procesos y caracterizaciones.",
    },
    # Calidad, NC y CAPA
    {
        "codigo": "calidad.ver",
        "nombre": "Ver desempeño de calidad",
        "descripcion": "Indicadores, objetivos y tableros de calidad.",
    },
    {
        "codigo": "noconformidades.reportar",
        "nombre": "Reportar no conformidad / evidencia",
        "descripcion": "Registro de NC, evidencias y hallazgos operativos.",
    },
    {
        "codigo": "noconformidades.gestion",
        "nombre": "Gestionar no conformidades y CAPA",
        "descripcion": "Análisis de causa, planes de acción y atención de hallazgos.",
    },
    {
        "codigo": "noconformidades.cerrar",
        "nombre": "Cerrar no conformidades",
        "descripcion": "Verificación de eficacia y cierre de NC / acciones.",
    },
    # Auditoría
    {
        "codigo": "auditorias.ver",
        "nombre": "Consultar auditorías",
        "descripcion": "Lectura de programas, informes y hallazgos.",
    },
    {
        "codigo": "auditorias.planificar",
        "nombre": "Planificar auditorías",
        "descripcion": "Plan anual, formularios y asignación de auditores.",
    },
    {
        "codigo": "auditorias.ejecutar",
        "nombre": "Ejecutar auditorías",
        "descripcion": "Carga de informes, evidencias y hallazgos de auditoría.",
    },
    # Riesgos ISO 31000 / 27001
    {
        "codigo": "riesgos.ver",
        "nombre": "Ver riesgos",
        "descripcion": "Consulta de matriz, historial y riesgos operativos.",
    },
    {
        "codigo": "riesgos.identificar",
        "nombre": "Identificar riesgos",
        "descripcion": "Registro de nuevos riesgos del proceso.",
    },
    {
        "codigo": "riesgos.gestion",
        "nombre": "Gestionar y mitigar riesgos",
        "descripcion": "Tratamiento, controles y continuidad del área o del SGC.",
    },
    # Formación
    {
        "codigo": "capacitaciones.gestion",
        "nombre": "Gestionar capacitaciones",
        "descripcion": "Planes de formación, asistencia y competencias.",
    },
]

CODIGOS_PERMISOS = [p["codigo"] for p in PERMISOS]

# Permisos heredados que ya no forman parte del catálogo SGC.
PERMISOS_OBSOLETOS = [
    "roles.administrar",
    "areas.ver",
    "documentos.editar",
    "documentos.eliminar",
    "indicadores.ver",
    "indicadores.medir",
    "no_conformidades.gestionar",
    "acciones_correctivas.gestionar",
    "objetivos.seguimiento",
    "procesos.gestionar",
    "riesgos.administrar",
    "capacitaciones.gestionar",
    "sistema.configurar",
    "sistema.migraciones",
    "tickets.soporte",
]

# ---------------------------------------------------------------------------
# Roles canónicos (documentación SGC-IUDC 2026)
# ---------------------------------------------------------------------------

ROLES: List[Dict] = [
    {
        "nombre": "Administrador SGC",
        "clave": "admin",
        "descripcion": (
            "Gobernanza total del SGC: configuración, identidades, matriz de "
            "permisos, logs, cierre de procesos y control documental maestro."
        ),
        "permisos": list(CODIGOS_PERMISOS),
    },
    {
        "nombre": "Líder de Proceso",
        "clave": "lider_proceso",
        "descripcion": (
            "Decano / director de área. Edita y aprueba documentos de su proceso, "
            "atiende hallazgos y mitiga riesgos de su área. No eleva privilegios "
            "ni consulta logs de auditoría de sistemas."
        ),
        "permisos": [
            "usuarios.ver",
            "documentos.ver",
            "documentos.crear",
            "documentos.revisar",
            "documentos.aprobar",
            "procesos.ver",
            "procesos.admin",
            "calidad.ver",
            "noconformidades.reportar",
            "noconformidades.gestion",
            "auditorias.ver",
            "riesgos.ver",
            "riesgos.identificar",
            "riesgos.gestion",
        ],
    },
    {
        "nombre": "Auditor",
        "clave": "auditor",
        "descripcion": (
            "Auditor interno o externo. Consulta total de evidencias y carga de "
            "informes/hallazgos. Sin modificación de documentación maestra ni "
            "planificación del programa de auditoría."
        ),
        "permisos": [
            "usuarios.ver",
            "documentos.ver",
            "procesos.ver",
            "calidad.ver",
            "noconformidades.reportar",
            "auditorias.ver",
            "auditorias.ejecutar",
            "riesgos.ver",
        ],
    },
    {
        "nombre": "Colaborador",
        "clave": "colaborador",
        "descripcion": (
            "Docente / administrativo. Consulta y descarga de formatos, carga de "
            "evidencias de trabajo diario y reporte de no conformidades."
        ),
        "permisos": [
            "documentos.ver",
            "documentos.crear",
            "procesos.ver",
            "noconformidades.reportar",
            "riesgos.ver",
            "riesgos.identificar",
        ],
    },
    {
        "nombre": "Invitado",
        "clave": "invitado",
        "descripcion": (
            "Público / estudiante / externo. Solo mapa de procesos y documentos "
            "de acceso libre. Sin auditoría, riesgos internos ni gestión."
        ),
        "permisos": [
            "procesos.ver",
        ],
    },
]

CLAVES_ROLES_CANONICOS = [r["clave"] for r in ROLES]

# Roles del seed anterior que se fusionan en el catálogo canónico.
MIGRACION_ROLES: Dict[str, str] = {
    "gestor_calidad": "admin",
    "coordinador": "lider_proceso",
    "auxiliar": "colaborador",
    "lider_siso": "lider_proceso",
}

# Alias aceptados en carga masiva / plantillas históricas.
ALIAS_ROLES: Dict[str, str] = {
    **MIGRACION_ROLES,
    "administrador sgc": "admin",
    "administrador": "admin",
    "admin sgc": "admin",
    "lider de proceso": "lider_proceso",
    "líder de proceso": "lider_proceso",
    "decano": "lider_proceso",
    "docente": "colaborador",
    "administrativo": "colaborador",
    "publico": "invitado",
    "público": "invitado",
    "estudiante": "invitado",
    "externo": "invitado",
}


def rol_por_clave(clave: str) -> Dict:
    for rol in ROLES:
        if rol["clave"] == clave:
            return rol
    raise KeyError(f"Rol canónico desconocido: {clave}")
