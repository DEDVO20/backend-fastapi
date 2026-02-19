from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.riesgo import Riesgo


class RiesgoRepository(BaseRepository[Riesgo]):
    def __init__(self, db: Session):
        super().__init__(db, Riesgo)
