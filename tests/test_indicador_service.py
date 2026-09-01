"""Pruebas de tendencia e historial de indicadores."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.services.indicador_service import IndicadorService


def _medicion(valor, periodo):
    return SimpleNamespace(valor=valor, periodo=periodo)


def test_tendencia_sin_datos():
    service = IndicadorService(db=MagicMock())
    indicador_id = uuid4()
    service.historial = lambda _id: []

    result = service.tendencia(indicador_id)

    assert result["tendencia"] == "sin_datos"
    assert result["total_mediciones"] == 0
    assert result["ultimo_valor"] is None


def test_tendencia_subiendo():
    service = IndicadorService(db=MagicMock())
    indicador_id = uuid4()
    service.historial = lambda _id: [_medicion(10, "2026-01"), _medicion(20, "2026-02")]

    result = service.tendencia(indicador_id)

    assert result["tendencia"] == "subiendo"
    assert result["total_mediciones"] == 2
    assert result["ultimo_valor"] == Decimal("20")
    assert result["promedio"] == Decimal("15.00")


def test_tendencia_bajando():
    service = IndicadorService(db=MagicMock())
    service.historial = lambda _id: [_medicion(30, "2026-01"), _medicion(12, "2026-02")]
    result = service.tendencia(uuid4())
    assert result["tendencia"] == "bajando"


def test_tendencia_estable():
    service = IndicadorService(db=MagicMock())
    service.historial = lambda _id: [_medicion(10, "2026-01"), _medicion(10, "2026-02")]
    result = service.tendencia(uuid4())
    assert result["tendencia"] == "estable"
