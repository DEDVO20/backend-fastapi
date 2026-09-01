"""Pruebas de endpoints públicos que no requieren autenticación."""


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["docs"] == "/docs"


def test_items_de_ejemplo(client):
    response = client.get("/api/v1/items")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_health_con_db_mockeada(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data


def test_docs_openapi(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Sistema de Gestión de Calidad"
    assert "/api/v1/auth/login" in schema["paths"]

    operation_ids = [
        operation["operationId"]
        for methods in schema["paths"].values()
        for operation in methods.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    duplicados = [oid for oid in operation_ids if operation_ids.count(oid) > 1]
    assert duplicados == []
