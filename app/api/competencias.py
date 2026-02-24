from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models.competencia import Competencia, EvaluacionCompetencia
from ..models.proceso import EtapaCompetencia, EtapaProceso, ResponsableProceso
from ..models.riesgo import RiesgoCompetenciaCritica
from ..schemas.competencia import (
    CompetenciaCreate, CompetenciaUpdate, CompetenciaResponse,
    EvaluacionCompetenciaCreate, EvaluacionCompetenciaUpdate, EvaluacionCompetenciaResponse,
    EtapaCompetenciaCreate, EtapaCompetenciaResponse,
    RiesgoCompetenciaCriticaCreate, RiesgoCompetenciaCriticaResponse,
)
from ..api.dependencies import require_any_permission
from ..models.usuario import Usuario
from ..services.competencia_service import CompetenciaService
from ..services.competency_risk_automation_service import CompetencyRiskAutomationService

router = APIRouter(
    prefix="/api/v1/competencias",
    tags=["competencias"],
    responses={404: {"description": "Not found"}},
)

# --- Gestor de Competencias (Catálogo) ---

@router.get("/", response_model=List[CompetenciaResponse])
def read_competencias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"]))):
    competencias = db.query(Competencia).order_by(Competencia.nombre).offset(skip).limit(limit).all()
    return competencias

@router.post("/", response_model=CompetenciaResponse, status_code=status.HTTP_201_CREATED)
def create_competencia(competencia: CompetenciaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"]))):
    db_competencia = db.query(Competencia).filter(Competencia.nombre == competencia.nombre).first()
    if db_competencia:
        raise HTTPException(status_code=400, detail="Competencia already exists")
    
    nuevo_item = Competencia(**competencia.model_dump())
    db.add(nuevo_item)
    db.commit()
    db.refresh(nuevo_item)
    return nuevo_item

@router.get("/{id}", response_model=CompetenciaResponse)
def read_competencia(id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"]))):
    db_competencia = db.query(Competencia).filter(Competencia.id == id).first()
    if db_competencia is None:
        raise HTTPException(status_code=404, detail="Competencia not found")
    return db_competencia

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_competencia(id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"]))):
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
    current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"]))
):
    query = db.query(EvaluacionCompetencia)
    
    if usuario_id:
        query = query.filter(EvaluacionCompetencia.usuario_id == usuario_id)
    if competencia_id:
        query = query.filter(EvaluacionCompetencia.competencia_id == competencia_id)
        
    evaluaciones = query.order_by(desc(EvaluacionCompetencia.fecha_evaluacion)).offset(skip).limit(limit).all()
    return evaluaciones

@router.post("/evaluar", response_model=EvaluacionCompetenciaResponse, status_code=status.HTTP_201_CREATED)
def evaluar_competencia(evaluacion: EvaluacionCompetenciaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"]))):
    service = CompetenciaService(db)
    return service.evaluar_competencia(evaluacion.model_dump(), current_user.id)

@router.delete("/evaluaciones/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluacion(id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"]))):
    db_evaluacion = db.query(EvaluacionCompetencia).filter(EvaluacionCompetencia.id == id).first()
    if db_evaluacion is None:
        raise HTTPException(status_code=404, detail="Evaluacion not found")
    
    db.delete(db_evaluacion)
    db.commit()
    return None


@router.get("/etapas/requisitos", response_model=List[EtapaCompetenciaResponse])
def listar_competencias_etapa(
    etapa_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"])),
):
    query = db.query(EtapaCompetencia).filter(EtapaCompetencia.activo.is_(True))
    if etapa_id:
        query = query.filter(EtapaCompetencia.etapa_id == etapa_id)
    return query.order_by(EtapaCompetencia.creado_en.desc()).all()


@router.post("/etapas/requisitos", response_model=EtapaCompetenciaResponse, status_code=status.HTTP_201_CREATED)
def crear_competencia_etapa(
    payload: EtapaCompetenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"])),
):
    existente = db.query(EtapaCompetencia).filter(
        EtapaCompetencia.etapa_id == payload.etapa_id,
        EtapaCompetencia.competencia_id == payload.competencia_id,
    ).first()
    if existente:
        existente.nivel_requerido = payload.nivel_requerido
        existente.activo = True
        item = existente
    else:
        item = EtapaCompetencia(**payload.model_dump())
        db.add(item)

    etapa = db.query(EtapaProceso).filter(EtapaProceso.id == payload.etapa_id).first()
    if etapa:
        automation = CompetencyRiskAutomationService(db)
        usuarios_asignados = db.query(ResponsableProceso.usuario_id).filter(
            ResponsableProceso.proceso_id == etapa.proceso_id,
            ResponsableProceso.activo.is_(True),
        ).distinct().all()
        for (usuario_id,) in usuarios_asignados:
            automation.evaluar_usuario_en_etapa(usuario_id, payload.etapa_id)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/etapas/requisitos/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_competencia_etapa(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"])),
):
    item = db.query(EtapaCompetencia).filter(EtapaCompetencia.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Relación etapa-competencia no encontrada")
    item.activo = False
    db.commit()
    return None


@router.get("/riesgos/criticas", response_model=List[RiesgoCompetenciaCriticaResponse])
def listar_competencias_criticas_riesgo(
    riesgo_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"])),
):
    query = db.query(RiesgoCompetenciaCritica).filter(RiesgoCompetenciaCritica.activo.is_(True))
    if riesgo_id:
        query = query.filter(RiesgoCompetenciaCritica.riesgo_id == riesgo_id)
    return query.order_by(RiesgoCompetenciaCritica.creado_en.desc()).all()


@router.post("/riesgos/criticas", response_model=RiesgoCompetenciaCriticaResponse, status_code=status.HTTP_201_CREATED)
def crear_competencia_critica_riesgo(
    payload: RiesgoCompetenciaCriticaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"])),
):
    existente = db.query(RiesgoCompetenciaCritica).filter(
        RiesgoCompetenciaCritica.riesgo_id == payload.riesgo_id,
        RiesgoCompetenciaCritica.competencia_id == payload.competencia_id,
    ).first()
    if existente:
        existente.nivel_minimo = payload.nivel_minimo
        existente.activo = True
        item = existente
    else:
        item = RiesgoCompetenciaCritica(**payload.model_dump())
        db.add(item)

    automation = CompetencyRiskAutomationService(db)
    automation.reevaluar_riesgo_critico(payload.riesgo_id)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/riesgos/criticas/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_competencia_critica_riesgo(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "procesos.admin", "riesgos.gestion", "sistema.admin"])),
):
    item = db.query(RiesgoCompetenciaCritica).filter(RiesgoCompetenciaCritica.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Relación riesgo-competencia crítica no encontrada")
    riesgo_id = item.riesgo_id
    item.activo = False
    automation = CompetencyRiskAutomationService(db)
    automation.reevaluar_riesgo_critico(riesgo_id)
    db.commit()
    return None
