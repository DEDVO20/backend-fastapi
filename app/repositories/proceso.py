from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.proceso import Proceso, EtapaProceso


class ProcesoRepository(BaseRepository[Proceso]):
    def __init__(self, db: Session):
        super().__init__(db, Proceso)


class EtapaProcesoRepository(BaseRepository[EtapaProceso]):
    def __init__(self, db: Session):
        super().__init__(db, EtapaProceso)
