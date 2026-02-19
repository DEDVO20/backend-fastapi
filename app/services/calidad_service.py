from sqlalchemy.orm import Session


class CalidadService:
    def __init__(self, db: Session):
        self.db = db
