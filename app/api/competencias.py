from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models.competencia import Competencia, EvaluacionCompetencia
from ..schemas.competencia import (
    CompetenciaCreate, CompetenciaUpdate, CompetenciaResponse,
    EvaluacionCompetenciaCreate, EvaluacionCompetenciaUpdate, EvaluacionCompetenciaResponse
)
from .auth import get_current_user
from ..models.usuario import Usuario

router = APIRouter(
    prefix="/api/v1/competencias",
    tags=["competencias"],
    responses={404: {"description": "Not found"}},
)

# --- Gestor de Competencias (Catálogo) ---

@router.get("/", response_model=List[CompetenciaResponse])
def read_competencias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    competencias = db.query(Competencia).order_by(Competencia.nombre).offset(skip).limit(limit).all()
    return competencias

@router.post("/", response_model=CompetenciaResponse, status_code=status.HTTP_201_CREATED)
def create_competencia(competencia: CompetenciaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_competencia = db.query(Competencia).filter(Competencia.nombre == competencia.nombre).first()
    if db_competencia:
        raise HTTPException(status_code=400, detail="Competencia already exists")
    
    nuevo_item = Competencia(**competencia.model_dump())
    db.add(nuevo_item)
    db.commit()
    db.refresh(nuevo_item)
    return nuevo_item

@router.get("/{id}", response_model=CompetenciaResponse)
def read_competencia(id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_competencia = db.query(Competencia).filter(Competencia.id == id).first()
    if db_competencia is None:
        raise HTTPException(status_code=404, detail="Competencia not found")
    return db_competencia

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_competencia(id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_competencia = db.query(Competencia).filter(Competencia.id == id).first()
    if db_competencia is None:
        raise HTTPException(status_code=404, detail="Competencia not found")
    
    db.delete(db_competencia)
    db.commit()
    return None

# --- Evaluaciones de Competencia ---

@router.get("/evaluaciones/listar", response_model=List[EvaluacionCompetenciaResponse])
def listar_evaluaciones(
    skip: int = 0, 
    limit: int = 100, 
    usuario_id: Optional[UUID] = None,
    competencia_id: Optional[UUID] = None,
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(EvaluacionCompetencia)
    
    if usuario_id:
        query = query.filter(EvaluacionCompetencia.usuario_id == usuario_id)
    if competencia_id:
        query = query.filter(EvaluacionCompetencia.competencia_id == competencia_id)
        
    evaluaciones = query.order_by(desc(EvaluacionCompetencia.fecha_evaluacion)).offset(skip).limit(limit).all()
    return evaluaciones

@router.post("/evaluar", response_model=EvaluacionCompetenciaResponse, status_code=status.HTTP_201_CREATED)
def evaluar_competencia(evaluacion: EvaluacionCompetenciaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # Check if user exists
    db_usuario = db.query(Usuario).filter(Usuario.id == evaluacion.usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario not found")
        
    # Check if competencia exists
    db_competencia = db.query(Competencia).filter(Competencia.id == evaluacion.competencia_id).first()
    if not db_competencia:
        raise HTTPException(status_code=404, detail="Competencia not found")

    nueva_evaluacion = EvaluacionCompetencia(**evaluacion.model_dump())
    if not nueva_evaluacion.evaluador_id:
        nueva_evaluacion.evaluador_id = current_user.id
        
    db.add(nueva_evaluacion)
    db.commit()
    db.refresh(nueva_evaluacion)
    return nueva_evaluacion

@router.delete("/evaluaciones/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluacion(id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_evaluacion = db.query(EvaluacionCompetencia).filter(EvaluacionCompetencia.id == id).first()
    if db_evaluacion is None:
        raise HTTPException(status_code=404, detail="Evaluacion not found")
    
    db.delete(db_evaluacion)
    db.commit()
    return None
