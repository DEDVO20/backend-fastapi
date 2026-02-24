"""Repositorio base con CRUD genérico."""
from typing import Generic, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def _base_query(self):
        query = self.db.query(self.model)
        if hasattr(self.model, "activo"):
            query = query.filter(self.model.activo.is_(True))
        return query

    def get_by_id(self, obj_id: UUID) -> Optional[ModelType]:
        return self._base_query().filter(self.model.id == obj_id).first()

    def get_all(self, skip: int = 0, limit: int = 100, **filters):
        query = self._base_query()
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.offset(skip).limit(limit).all()

    def create(self, data: dict, creado_por: Optional[UUID] = None) -> ModelType:
        payload = dict(data)
        if creado_por and hasattr(self.model, "creado_por") and "creado_por" not in payload:
            payload["creado_por"] = creado_por
        db_obj = self.model(**payload)
        self.db.add(db_obj)
        self.db.flush()
        return db_obj

    def update(self, obj_id: UUID, data: dict) -> Optional[ModelType]:
        obj = self.get_by_id(obj_id)
        if not obj:
            return None
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        self.db.flush()
        return obj

    def soft_delete(self, obj_id: UUID) -> Optional[ModelType]:
        obj = self.get_by_id(obj_id)
        if not obj:
            return None
        if hasattr(obj, "activo"):
            setattr(obj, "activo", False)
            self.db.flush()
            return obj
        self.db.delete(obj)
        self.db.flush()
        return obj
