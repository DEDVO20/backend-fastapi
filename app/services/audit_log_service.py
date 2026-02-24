from sqlalchemy.orm import Session

from ..models.audit_log import AuditLog


class AuditLogService:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, skip: int = 0, limit: int = 100):
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
