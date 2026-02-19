from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.auditoria import Auditoria


class AuditoriaRepository(BaseRepository[Auditoria]):
    def __init__(self, db: Session):
        super().__init__(db, Auditoria)
