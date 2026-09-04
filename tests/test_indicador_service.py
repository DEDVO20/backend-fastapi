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


def test_indicador_response_acepta_tipo_antiguo():
    from datetime import datetime, timezone
    from app.schemas.calidad import IndicadorResponse

    ahora = datetime.now(timezone.utc)
    data = IndicadorResponse.model_validate(
        {
            "id": uuid4(),
            "proceso_id": uuid4(),
            "codigo": "IND-1",
            "nombre": "Prueba",
            "frecuencia_medicion": "mensual",
            "tipo_indicador": "calidad",
            "estado": "viejo",
            "activo": True,
            "creado_en": ahora,
            "actualizado_en": ahora,
        }
    )
    assert data.tipo_indicador == "eficacia"
    assert data.estado == "borrador"


def test_aprobar_exige_otra_persona():
    creador_id = uuid4()
    indicador = SimpleNamespace(
        id=uuid4(),
        estado="pendiente_aprobacion",
        creado_por=creador_id,
        mediciones=[SimpleNamespace(valor=10, periodo="2026-01")],
        responsable_medicion_id=None,
        revisado_por=None,
        fecha_revision=None,
    )
    service = IndicadorService(db=MagicMock())
    service.obtener = lambda _id: indicador
    service.historial = lambda _id: [SimpleNamespace(valor=10, periodo="2026-01")]

    try:
        service.aprobar(indicador.id, creador_id)
        assert False, "Debió rechazar autoaprobación"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403


def test_solicitar_aprobacion_exige_medicion():
    indicador = SimpleNamespace(id=uuid4(), estado="borrador", mediciones=[])
    service = IndicadorService(db=MagicMock())
    service.obtener = lambda _id: indicador
    service.historial = lambda _id: []
    try:
        service.solicitar_aprobacion(indicador.id, uuid4())
        assert False, "Debió exigir medición"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400


def test_historial_fallback_si_falla_query():
    db_mock = MagicMock()
    # Simular fallo en primer query y éxito en el query de fallback
    query_first = MagicMock()
    query_first.options.return_value.filter.return_value.order_by.return_value.unique.return_value.all.side_effect = Exception("DB error")
    
    query_fallback = MagicMock()
    query_fallback.filter.return_value.order_by.return_value.all.return_value = ["medicion1"]
    
    db_mock.query.side_effect = [query_first, query_fallback]
    
    service = IndicadorService(db=db_mock)
    service.obtener = lambda _id: None
    
    res = service.historial(uuid4())
    assert res == ["medicion1"]

