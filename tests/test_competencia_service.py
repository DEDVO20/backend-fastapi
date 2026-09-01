"""Pruebas de normalización y comparación de niveles de competencia."""
from unittest.mock import MagicMock

from app.services.competencia_service import CompetenciaService


def test_normalizar_nivel():
    service = CompetenciaService(db=MagicMock())
    assert service._normalizar_nivel("  Avanzado ") == "avanzado"
    assert service._normalizar_nivel(None) is None
    assert service._normalizar_nivel("") is None


def test_orden_de_niveles():
    assert CompetenciaService.NIVELES_ORDEN["basico"] < CompetenciaService.NIVELES_ORDEN["intermedio"]
    assert CompetenciaService.NIVELES_ORDEN["intermedio"] < CompetenciaService.NIVELES_ORDEN["avanzado"]


def test_brecha_cuando_nivel_actual_es_menor():
    actual = CompetenciaService.NIVELES_ORDEN["basico"]
    requerido = CompetenciaService.NIVELES_ORDEN["avanzado"]
    assert actual < requerido
