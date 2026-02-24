"""
Modelos de la base de datos - Sistema de Gestión de Calidad
"""

# Importar modelo base
from .base import BaseModel, UUIDMixin, TimestampMixin

# Importar modelos de usuarios y autenticación
from .usuario import (
    Area,
    Usuario,
    Rol,
    Permiso,
    UsuarioRol,
    RolPermiso
)

# Importar modelos de procesos
from .proceso import (
    Proceso,
    EtapaProceso,
    EtapaCompetencia,
    InstanciaProceso,
    ParticipanteProceso,
    ResponsableProceso,
    AccionProceso
)

# Importar modelos de documentos
from .documento import (
    Documento,
    VersionDocumento,
    DocumentoProceso
)

# Importar modelos de calidad
from .calidad import (
    Indicador,
    MedicionIndicador,
    NoConformidad,
    AccionCorrectiva,
    ObjetivoCalidad,
    SeguimientoObjetivo
)

# Importar modelos de auditorías
from .auditoria import (
    Auditoria,
    HallazgoAuditoria,
    ProgramaAuditoria
)
from .historial import HistorialEstado
from .audit_log import AuditLog

# Importar modelos de riesgos
from .riesgo import (
    Riesgo,
    ControlRiesgo,
    EvaluacionRiesgoHistorial,
    RiesgoCompetenciaCritica,
)

# Importar modelos de capacitación
from .capacitacion import (
    Capacitacion,
    AsistenciaCapacitacion
)

# Importar modelos de competencias
from .competencia import (
    Competencia,
    EvaluacionCompetencia,
    BrechaCompetencia,
)

# Importar modelos de Tickets
from .ticket import Ticket, EstadoTicket, TipoTicket, PrioridadTicket

# Importar modelos del sistema
from .sistema import (
    Notificacion,
    Configuracion,
    FormularioDinamico,
    CampoFormulario,
    RespuestaFormulario,
    Asignacion
)

# Lista de todos los modelos para facilitar operaciones masivas
__all__ = [
    # Base
    "BaseModel",
    "UUIDMixin",
    "TimestampMixin",
    # Usuarios y autenticación
    "Area",
    "Usuario",
    "Rol",
    "Permiso",
    "UsuarioRol",
    "RolPermiso",
    # Procesos
    "Proceso",
    "EtapaProceso",
    "EtapaCompetencia",
    "InstanciaProceso",
    "ParticipanteProceso",
    "ResponsableProceso",
    "AccionProceso",
    # Documentos
    "Documento",
    "VersionDocumento",
    "DocumentoProceso",
    # Calidad
    "Indicador",
    "MedicionIndicador",
    "NoConformidad",
    "AccionCorrectiva",
    "ObjetivoCalidad",
    "SeguimientoObjetivo",
    # Auditorías
    "Auditoria",
    "HallazgoAuditoria",
    "ProgramaAuditoria",
    "HistorialEstado",
    "AuditLog",
    # Riesgos
    "Riesgo",
    "ControlRiesgo",
    "EvaluacionRiesgoHistorial",
    "RiesgoCompetenciaCritica",
    # Capacitación
    "Capacitacion",
    "AsistenciaCapacitacion",
    # Competencias
    "Competencia",
    "EvaluacionCompetencia",
    "BrechaCompetencia",
    # Tickets
    "Ticket",
    "EstadoTicket",
    "TipoTicket",
    "PrioridadTicket",
    # Sistema
    "Notificacion",
    "Configuracion",
    "FormularioDinamico",
    "CampoFormulario",
    "RespuestaFormulario",
    "Asignacion",
]
