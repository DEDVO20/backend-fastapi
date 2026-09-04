"""Pruebas de cierre y verificación de acciones correctivas."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.calidad_service import CalidadService


def _query_returning(first_value):
    query = MagicMock()
    query.filter.return_value.first.return_value = first_value
    return query


def test_cerrar_accion_no_encontrada():
    db = MagicMock()
    db.query.return_value = _query_returning(None)
    service = CalidadService(db)

    with pytest.raises(HTTPException) as exc:
        service.cerrar_accion(uuid4(), {"eficacia_verificada": 90}, uuid4())
    assert exc.value.status_code == 404


def test_cerrar_accion_sin_analisis_causa():
    accion = SimpleNamespace(
        analisis_causa_raiz=None,
        evidencias="ok",
        no_conformidad_id=None,
    )
    db = MagicMock()
    db.query.return_value = _query_returning(accion)
    service = CalidadService(db)

    with pytest.raises(HTTPException) as exc:
        service.cerrar_accion(uuid4(), {"eficacia_verificada": 90}, uuid4())
    assert exc.value.status_code == 400
    assert "causa" in exc.value.detail.lower()


def test_cerrar_accion_sin_evidencias():
    accion = SimpleNamespace(
        analisis_causa_raiz="5 porqués",
        evidencias=None,
        no_conformidad_id=None,
    )
    db = MagicMock()
    db.query.return_value = _query_returning(accion)
    service = CalidadService(db)

    with pytest.raises(HTTPException) as exc:
        service.cerrar_accion(uuid4(), {"eficacia_verificada": 90}, uuid4())
    assert exc.value.status_code == 400


def test_cerrar_accion_evidencias_json_vacio():
    from app.services.calidad_service import tiene_evidencias

    assert not tiene_evidencias(None)
    assert not tiene_evidencias("")
    assert not tiene_evidencias("[]")
    assert tiene_evidencias('[{"url":"x"}]')


def test_cerrar_accion_eficaz_cierra():
    accion = SimpleNamespace(
        id=uuid4(),
        analisis_causa_raiz="causa",
        evidencias="foto",
        no_conformidad_id=None,
        observacion=None,
        eficacia_verificada=None,
        estado="abierta",
        verificado_por=None,
        fecha_verificacion=None,
    )
    db = MagicMock()
    db.query.return_value = _query_returning(accion)
    service = CalidadService(db)

    with patch("app.services.calidad_service.registrar_auditoria"):
        result = service.cerrar_accion(accion.id, {"eficacia_verificada": 85}, uuid4())

    assert result.estado == "cerrada"
    db.commit.assert_called_once()


def test_cerrar_accion_no_eficaz():
    nc = SimpleNamespace(estado="en_proceso")
    accion = SimpleNamespace(
        id=uuid4(),
        analisis_causa_raiz="causa",
        evidencias="foto",
        no_conformidad_id=uuid4(),
        observacion=None,
        eficacia_verificada=None,
        estado="abierta",
        verificado_por=None,
        fecha_verificacion=None,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [accion, nc]
    service = CalidadService(db)

    with patch("app.services.calidad_service.registrar_auditoria"):
        result = service.cerrar_accion(accion.id, {"eficaz": False}, uuid4())

    assert result.estado == "no_eficaz"
    assert nc.estado == "abierta"
