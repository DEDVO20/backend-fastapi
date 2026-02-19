from sqlalchemy.orm import Session


class CapacitacionService:
    def __init__(self, db: Session):
        self.db = db
