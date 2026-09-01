"""Pruebas de autorización en endpoints protegidos."""
from unittest.mock import MagicMock, patch

from app.database import get_db
from app.main import app


ENDPOINTS_PROTEGIDOS = [
    ("GET", "/api/v1/usuarios"),
    ("GET", "/api/v1/usuarios/carga-masiva/plantilla"),
    ("GET", "/api/v1/usuarios/carga-masiva/exportar"),
    ("GET", "/api/v1/areas"),
    ("GET", "/api/v1/procesos"),
    ("GET", "/api/v1/riesgos"),
    ("GET", "/api/v1/tickets"),
    ("GET", "/api/v1/notificaciones"),
    ("GET", "/api/v1/competencias"),
    ("GET", "/api/v1/analytics/calidad"),
]


def test_endpoints_protegidos_sin_token_rechazan(client):
    for method, path in ENDPOINTS_PROTEGIDOS:
        response = client.request(method, path)
        assert response.status_code in (401, 403), f"{path} debió exigir autenticación"


def test_listar_procesos_sin_permiso(client_sin_permisos):
    response = client_sin_permisos.get("/api/v1/procesos")
    assert response.status_code == 403
    assert "permisos" in response.json()["detail"].lower()


def test_listar_riesgos_como_admin(client_admin):
    db = MagicMock()
    db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    try:
        with patch("app.api.riesgos.RiesgoService.listar", return_value=[]):
            response = client_admin.get("/api/v1/riesgos")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json() == []
