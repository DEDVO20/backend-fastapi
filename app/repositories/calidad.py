from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.calidad import NoConformidad


class CalidadRepository(BaseRepository[NoConformidad]):
    def __init__(self, db: Session):
        super().__init__(db, NoConformidad)
