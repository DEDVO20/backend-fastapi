"""Pruebas de la API de notificaciones del usuario autenticado."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.database import get_db
from app.main import app


def _notificacion(usuario_id, **kwargs):
    now = datetime.now(timezone.utc)
    data = dict(
        id=kwargs.get("id", uuid4()),
        usuario_id=usuario_id,
        titulo=kwargs.get("titulo", "Ticket asignado"),
        mensaje=kwargs.get("mensaje", "Se te ha asignado un ticket"),
        tipo=kwargs.get("tipo", "asignacion"),
        leida=kwargs.get("leida", False),
        fecha_lectura=kwargs.get("fecha_lectura"),
        referencia_tipo=kwargs.get("referencia_tipo", "ticket"),
        referencia_id=kwargs.get("referencia_id", uuid4()),
        creado_en=kwargs.get("creado_en", now),
    )
    return SimpleNamespace(**data)


def _override_db(db):
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override


def test_usuario_sin_admin_puede_listar_sus_notificaciones(client_sin_permisos, usuario_sin_permisos):
    notif = _notificacion(usuario_sin_permisos.id)
    db = MagicMock()
    query = db.query.return_value.filter.return_value
    query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [notif]
    _override_db(db)
    try:
        response = client_sin_permisos.get("/api/v1/notificaciones")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["titulo"] == "Ticket asignado"
    assert data[0]["usuario_id"] == str(usuario_sin_permisos.id)


def test_marcar_todas_leidas_no_choca_con_ruta_uuid(client_sin_permisos):
    db = MagicMock()
    db.query.return_value.filter.return_value.update.return_value = 2
    _override_db(db)
    try:
        response = client_sin_permisos.put("/api/v1/notificaciones/marcar-todas-leidas")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200, response.text
    assert "2 notificaciones" in response.json()["message"]
    db.commit.assert_called_once()


def test_marcar_todas_leidas_tambien_acepta_post(client_sin_permisos):
    db = MagicMock()
    db.query.return_value.filter.return_value.update.return_value = 3
    _override_db(db)
    try:
        response = client_sin_permisos.post("/api/v1/notificaciones/marcar-todas-leidas")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200, response.text
    assert "3 notificaciones" in response.json()["message"]
    db.commit.assert_called_once()


def test_marcar_una_notificacion_como_leida(client_sin_permisos, usuario_sin_permisos):
    notif = _notificacion(usuario_sin_permisos.id)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = notif
    _override_db(db)
    try:
        response = client_sin_permisos.put(f"/api/v1/notificaciones/{notif.id}/marcar-leida")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200, response.text
    assert response.json()["leida"] is True
    assert notif.leida is True
    assert notif.fecha_lectura is not None
    db.commit.assert_called_once()


def test_marcar_notificacion_ajena_devuelve_404(client_sin_permisos):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    _override_db(db)
    try:
        response = client_sin_permisos.put(f"/api/v1/notificaciones/{uuid4()}/marcar-leida")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 404


def test_actualizar_propia_con_leida_true(client_sin_permisos, usuario_sin_permisos):
    notif = _notificacion(usuario_sin_permisos.id)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = notif
    _override_db(db)
    try:
        response = client_sin_permisos.put(
            f"/api/v1/notificaciones/{notif.id}",
            json={"leida": True},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200, response.text
    assert response.json()["leida"] is True
    assert notif.leida is True
    db.commit.assert_called_once()
