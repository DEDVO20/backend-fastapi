from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.usuario import Usuario


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, db: Session):
        super().__init__(db, Usuario)
