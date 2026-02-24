from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.capacitacion import Capacitacion


class CapacitacionRepository(BaseRepository[Capacitacion]):
    def __init__(self, db: Session):
        super().__init__(db, Capacitacion)
