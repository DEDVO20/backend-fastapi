from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.competencia import EvaluacionCompetencia


class CompetenciaRepository(BaseRepository[EvaluacionCompetencia]):
    def __init__(self, db: Session):
        super().__init__(db, EvaluacionCompetencia)
