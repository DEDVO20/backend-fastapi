from sqlalchemy.orm import Session


class IndicadorService:
    def __init__(self, db: Session):
        self.db = db
