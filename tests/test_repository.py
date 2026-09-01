"""Pruebas del repositorio base con sesión mockeada."""
from unittest.mock import MagicMock
from uuid import uuid4

from app.repositories.base import BaseRepository


class DummyModel:
    activo = True
    creado_por = None

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid4())
        self.nombre = kwargs.get("nombre")
        self.activo = kwargs.get("activo", True)
        self.creado_por = kwargs.get("creado_por")


def test_create_asigna_creado_por():
    db = MagicMock()
    repo = BaseRepository(db, DummyModel)
    usuario_id = uuid4()

    obj = repo.create({"nombre": "Nuevo"}, creado_por=usuario_id)

    db.add.assert_called_once()
    db.flush.assert_called_once()
    assert obj.nombre == "Nuevo"
    assert obj.creado_por == usuario_id


def test_update_modifica_campos_existentes():
    existente = DummyModel(nombre="Antes")
    db = MagicMock()
    repo = BaseRepository(db, DummyModel)
    repo.get_by_id = lambda _id: existente

    updated = repo.update(existente.id, {"nombre": "Después", "no_existe": 1})

    assert updated.nombre == "Después"
    assert not hasattr(updated, "no_existe")
    db.flush.assert_called_once()


def test_update_inexistente_devuelve_none():
    db = MagicMock()
    repo = BaseRepository(db, DummyModel)
    repo.get_by_id = lambda _id: None
    assert repo.update(uuid4(), {"nombre": "X"}) is None


def test_soft_delete_marca_inactivo():
    existente = DummyModel(activo=True)
    db = MagicMock()
    repo = BaseRepository(db, DummyModel)
    repo.get_by_id = lambda _id: existente

    result = repo.soft_delete(existente.id)

    assert result.activo is False
    db.flush.assert_called_once()
    db.delete.assert_not_called()
