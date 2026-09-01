"""Pruebas del helper de notificaciones de asignación."""
from uuid import uuid4
from unittest.mock import MagicMock, patch

from app.utils.notification_service import notificar_asignacion, notificar_asignaciones


def test_no_notifica_si_falta_usuario():
    db = MagicMock()
    assert notificar_asignacion(db, None, "t", "m", "ticket", uuid4()) is None
    db.add.assert_not_called()


def test_no_notifica_si_es_el_mismo_responsable():
    db = MagicMock()
    usuario = uuid4()
    assert notificar_asignacion(
        db,
        usuario,
        "t",
        "m",
        "ticket",
        uuid4(),
        anterior_usuario_id=usuario,
    ) is None
    db.add.assert_not_called()


def test_no_notifica_si_el_actor_se_asigna_a_si_mismo():
    db = MagicMock()
    usuario = uuid4()
    assert notificar_asignacion(
        db,
        usuario,
        "t",
        "m",
        "ticket",
        uuid4(),
        actor_id=usuario,
    ) is None
    db.add.assert_not_called()


@patch("app.utils.notification_service.Notificacion")
def test_crea_notificacion_cuando_hay_nuevo_asignado(mock_notif):
    db = MagicMock()
    instancia = MagicMock()
    mock_notif.return_value = instancia
    destinatario = uuid4()
    actor = uuid4()
    ref = uuid4()

    result = notificar_asignacion(
        db,
        destinatario,
        "Asignado",
        "Se te asignó un ticket",
        "ticket",
        ref,
        actor_id=actor,
    )

    assert result is instancia
    db.add.assert_called_once_with(instancia)
    db.commit.assert_called_once()


@patch("app.utils.notification_service.Notificacion")
def test_notificar_asignaciones_omite_duplicados_y_anteriores(mock_notif):
    db = MagicMock()
    mock_notif.return_value = MagicMock()
    a = uuid4()
    b = uuid4()
    actor = uuid4()
    ref = uuid4()

    notificar_asignaciones(
        db,
        [a, a, b, None],
        "Equipo",
        "Formas parte del equipo",
        "auditoria",
        ref,
        actor_id=actor,
        anteriores=[a],
    )

    assert db.add.call_count == 1
