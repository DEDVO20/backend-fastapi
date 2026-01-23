"""
Modelos base y mixins reutilizables para SQLAlchemy
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from ..database import Base


class UUIDMixin:
    """Mixin para agregar UUID como primary key"""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    """Mixin para agregar timestamps de creación y actualización"""
    
    @declared_attr
    def creado_en(cls):
        return Column('creado_en', DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    @declared_attr
    def actualizado_en(cls):
        return Column('actualizado_en', DateTime(timezone=True), nullable=False, 
                     default=datetime.utcnow, onupdate=datetime.utcnow)


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Modelo base abstracto con UUID y timestamps"""
    __abstract__ = True
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
