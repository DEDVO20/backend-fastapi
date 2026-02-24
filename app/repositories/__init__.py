"""Capa de acceso a datos (repositories)."""

from .base import BaseRepository
from .proceso import ProcesoRepository, EtapaProcesoRepository
from .riesgo import RiesgoRepository
from .auditoria import AuditoriaRepository
from .calidad import CalidadRepository
from .competencia import CompetenciaRepository
from .capacitacion import CapacitacionRepository
from .usuario import UsuarioRepository

__all__ = [
    "BaseRepository",
    "ProcesoRepository",
    "EtapaProcesoRepository",
    "RiesgoRepository",
    "AuditoriaRepository",
    "CalidadRepository",
    "CompetenciaRepository",
    "CapacitacionRepository",
    "UsuarioRepository",
]
