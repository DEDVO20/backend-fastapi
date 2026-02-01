"""
Endpoints CRUD para gestión de calidad
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.calidad import Indicador, NoConformidad, AccionCorrectiva, ObjetivoCalidad, SeguimientoObjetivo
from ..schemas.calidad import (
    IndicadorCreate,
    IndicadorUpdate,
    IndicadorResponse,
    NoConformidadCreate,
    NoConformidadUpdate,
    NoConformidadResponse,
    AccionCorrectivaCreate,
    AccionCorrectivaUpdate,
    AccionCorrectivaResponse,
    AccionCorrectivaEstadoUpdate,
    AccionCorrectivaVerificacion,
    ObjetivoCalidadCreate,
    ObjetivoCalidadUpdate,

    ObjetivoCalidadResponse,
    SeguimientoObjetivoCreate,
    SeguimientoObjetivoUpdate,
    SeguimientoObjetivoResponse
)
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario

router = APIRouter(prefix="/api/v1", tags=["calidad"])


# ======================
# Endpoints de Indicadores
# ======================

@router.get("/indicadores", response_model=List[IndicadorResponse])
def listar_indicadores(
    skip: int = 0,
    limit: int = 100,
    proceso_id: UUID = None,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar indicadores de desempeño"""
    query = db.query(Indicador)
    
    if proceso_id:
        query = query.filter(Indicador.proceso_id == proceso_id)
    if activo is not None:
        query = query.filter(Indicador.activo == activo)
    
    indicadores = query.offset(skip).limit(limit).all()
    return indicadores


@router.post("/indicadores", response_model=IndicadorResponse, status_code=status.HTTP_201_CREATED)
def crear_indicador(
    indicador: IndicadorCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo indicador"""
    # Verificar código único
    db_indicador = db.query(Indicador).filter(Indicador.codigo == indicador.codigo).first()
    if db_indicador:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de indicador ya existe"
        )
    
    nuevo_indicador = Indicador(**indicador.model_dump())
    db.add(nuevo_indicador)
    db.commit()
    db.refresh(nuevo_indicador)
    return nuevo_indicador


@router.get("/indicadores/{indicador_id}", response_model=IndicadorResponse)
def obtener_indicador(
    indicador_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un indicador por ID"""
    indicador = db.query(Indicador).filter(Indicador.id == indicador_id).first()
    if not indicador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Indicador no encontrado"
        )
    return indicador


@router.put("/indicadores/{indicador_id}", response_model=IndicadorResponse)
def actualizar_indicador(
    indicador_id: UUID,
    indicador_update: IndicadorUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un indicador"""
    indicador = db.query(Indicador).filter(Indicador.id == indicador_id).first()
    if not indicador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Indicador no encontrado"
        )
    
    update_data = indicador_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(indicador, field, value)
    
    db.commit()
    db.refresh(indicador)
    return indicador


@router.delete("/indicadores/{indicador_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_indicador(
    indicador_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un indicador"""
    indicador = db.query(Indicador).filter(Indicador.id == indicador_id).first()
    if not indicador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Indicador no encontrado"
        )
    
    db.delete(indicador)
    db.commit()
    return None


# =============================
# Endpoints de No Conformidades
# =============================

@router.get("/no-conformidades", response_model=List[NoConformidadResponse])
def listar_no_conformidades(
    skip: int = 0,
    limit: int = 100,
    proceso_id: UUID = None,
    estado: str = None,
    tipo: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar no conformidades"""
    query = db.query(NoConformidad)
    
    if proceso_id:
        query = query.filter(NoConformidad.proceso_id == proceso_id)
    if estado:
        query = query.filter(NoConformidad.estado == estado)
    if tipo:
        query = query.filter(NoConformidad.tipo == tipo)
    
    no_conformidades = query.offset(skip).limit(limit).all()
    return no_conformidades


@router.post("/no-conformidades", response_model=NoConformidadResponse, status_code=status.HTTP_201_CREATED)
def crear_no_conformidad(
    nc: NoConformidadCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva no conformidad"""
    # Verify permission "noconformidades.reportar"
    tiene_permiso = any(p.codigo == "noconformidades.reportar" for r in current_user.roles for p in r.permisos)
    if not tiene_permiso:
        raise HTTPException(status_code=403, detail="No tienes permiso para reportar no conformidades")

    # Verificar código único
    db_nc = db.query(NoConformidad).filter(NoConformidad.codigo == nc.codigo).first()
    if db_nc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de no conformidad ya existe"
        )
    
    nueva_nc = NoConformidad(**nc.model_dump())
    db.add(nueva_nc)
    db.commit()
    db.refresh(nueva_nc)
    return nueva_nc


@router.get("/no-conformidades/{nc_id}", response_model=NoConformidadResponse)
def obtener_no_conformidad(
    nc_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener una no conformidad por ID"""
    nc = db.query(NoConformidad).filter(NoConformidad.id == nc_id).first()
    if not nc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No conformidad no encontrada"
        )
    return nc


@router.put("/no-conformidades/{nc_id}", response_model=NoConformidadResponse)
def actualizar_no_conformidad(
    nc_id: UUID,
    nc_update: NoConformidadUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar una no conformidad"""
    nc = db.query(NoConformidad).filter(NoConformidad.id == nc_id).first()
    if not nc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No conformidad no encontrada"
        )
    
    update_data = nc_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(nc, field, value)
    
    db.commit()
    db.refresh(nc)
    return nc


# ================================
# Endpoints de Acciones Correctivas
# ================================

@router.get("/acciones-correctivas", response_model=List[AccionCorrectivaResponse])
def listar_acciones_correctivas(
    skip: int = 0,
    limit: int = 100,
    no_conformidad_id: UUID = None,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar acciones correctivas"""
    query = db.query(AccionCorrectiva)
    
    if no_conformidad_id:
        query = query.filter(AccionCorrectiva.no_conformidad_id == no_conformidad_id)
    if estado:
        query = query.filter(AccionCorrectiva.estado == estado)
    
    acciones = query.offset(skip).limit(limit).all()
    return acciones


@router.post("/acciones-correctivas", response_model=AccionCorrectivaResponse, status_code=status.HTTP_201_CREATED)
def crear_accion_correctiva(
    accion: AccionCorrectivaCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva acción correctiva"""
    # Verificar código único
    db_accion = db.query(AccionCorrectiva).filter(AccionCorrectiva.codigo == accion.codigo).first()
    if db_accion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de acción correctiva ya existe"
        )
    
    nueva_accion = AccionCorrectiva(**accion.model_dump())
    db.add(nueva_accion)
    db.commit()
    db.refresh(nueva_accion)
    return nueva_accion


@router.get("/acciones-correctivas/{accion_id}", response_model=AccionCorrectivaResponse)
def obtener_accion_correctiva(
    accion_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener una acción correctiva por ID"""
    accion = db.query(AccionCorrectiva).filter(AccionCorrectiva.id == accion_id).first()
    if not accion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acción correctiva no encontrada"
        )
    return accion


@router.put("/acciones-correctivas/{accion_id}", response_model=AccionCorrectivaResponse)
def actualizar_accion_correctiva(
    accion_id: UUID,
    accion_update: AccionCorrectivaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar una acción correctiva"""
    accion = db.query(AccionCorrectiva).filter(AccionCorrectiva.id == accion_id).first()
    if not accion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acción correctiva no encontrada"
        )
    
    update_data = accion_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(accion, field, value)
    
    db.commit()
    db.refresh(accion)
    return accion


@router.patch("/acciones-correctivas/{accion_id}/estado", response_model=AccionCorrectivaResponse)
def cambiar_estado_accion_correctiva(
    accion_id: UUID,
    estado_update: AccionCorrectivaEstadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Cambiar estado de una acción correctiva"""
    accion = db.query(AccionCorrectiva).filter(AccionCorrectiva.id == accion_id).first()
    if not accion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acción correctiva no encontrada"
        )
    
    accion.estado = estado_update.estado
    db.commit()
    db.refresh(accion)
    return accion


@router.patch("/acciones-correctivas/{accion_id}/verificar", response_model=AccionCorrectivaResponse)
def verificar_accion_correctiva(
    accion_id: UUID,
    verificacion: AccionCorrectivaVerificacion,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Verificar una acción correctiva"""
    # Verify permission "noconformidades.cerrar"
    tiene_permiso = any(p.codigo == "noconformidades.cerrar" for r in current_user.roles for p in r.permisos)
    if not tiene_permiso:
        raise HTTPException(status_code=403, detail="No tienes permiso para cerrar no conformidades")

    accion = db.query(AccionCorrectiva).filter(AccionCorrectiva.id == accion_id).first()
    if not accion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acción correctiva no encontrada"
        )
    
    from datetime import date
    accion.fecha_verificacion = date.today()
    if verificacion.observaciones:
        accion.observacion = verificacion.observaciones
    
    # Logic for closure or state change could go here
    
    db.commit()
    db.refresh(accion)
    return accion


# ================================
# Endpoints de Objetivos de Calidad
# ================================

@router.get("/objetivos-calidad", response_model=List[ObjetivoCalidadResponse])
def listar_objetivos_calidad(
    skip: int = 0,
    limit: int = 100,
    area_id: UUID = None,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar objetivos de calidad"""
    query = db.query(ObjetivoCalidad)
    
    if area_id:
        query = query.filter(ObjetivoCalidad.area_id == area_id)
    if estado:
        query = query.filter(ObjetivoCalidad.estado == estado)
    
    objetivos = query.offset(skip).limit(limit).all()
    return objetivos


@router.post("/objetivos-calidad", response_model=ObjetivoCalidadResponse, status_code=status.HTTP_201_CREATED)
def crear_objetivo_calidad(
    objetivo: ObjetivoCalidadCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo objetivo de calidad"""
    # Verificar código único
    db_objetivo = db.query(ObjetivoCalidad).filter(ObjetivoCalidad.codigo == objetivo.codigo).first()
    if db_objetivo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de objetivo ya existe"
        )
    
    nuevo_objetivo = ObjetivoCalidad(**objetivo.model_dump())
    db.add(nuevo_objetivo)
    db.commit()
    db.refresh(nuevo_objetivo)
    return nuevo_objetivo


@router.get("/objetivos-calidad/{objetivo_id}", response_model=ObjetivoCalidadResponse)
def obtener_objetivo_calidad(
    objetivo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un objetivo de calidad por ID"""
    objetivo = db.query(ObjetivoCalidad).filter(ObjetivoCalidad.id == objetivo_id).first()
    if not objetivo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objetivo de calidad no encontrado"
        )
    return objetivo


@router.put("/objetivos-calidad/{objetivo_id}", response_model=ObjetivoCalidadResponse)
def actualizar_objetivo_calidad(
    objetivo_id: UUID,
    objetivo_update: ObjetivoCalidadUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un objetivo de calidad"""
    objetivo = db.query(ObjetivoCalidad).filter(ObjetivoCalidad.id == objetivo_id).first()
    if not objetivo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objetivo de calidad no encontrado"
        )
    
    update_data = objetivo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(objetivo, field, value)
    
    db.commit()
    db.refresh(objetivo)
    return objetivo


@router.delete("/objetivos-calidad/{objetivo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_objetivo_calidad(
    objetivo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un objetivo de calidad"""
    objetivo = db.query(ObjetivoCalidad).filter(ObjetivoCalidad.id == objetivo_id).first()
    if not objetivo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objetivo de calidad no encontrado"
        )
    
    db.delete(objetivo)
    db.commit()
    return None



# ================================
# Endpoints de Seguimiento Objetivos
# ================================

@router.get("/seguimientos-objetivo", response_model=List[SeguimientoObjetivoResponse])
def listar_seguimientos_objetivo(
    skip: int = 0,
    limit: int = 100,
    objetivo_id: UUID = None,
    # TODO: filtrar por fecha?
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar seguimientos de objetivos"""
    query = db.query(SeguimientoObjetivo)
    
    if objetivo_id:
        query = query.filter(SeguimientoObjetivo.objetivo_calidad_id == objetivo_id)
    
    # Ordenar por fecha descendente
    query = query.order_by(SeguimientoObjetivo.fecha_seguimiento.desc())
    
    seguimientos = query.offset(skip).limit(limit).all()
    return seguimientos


@router.post("/seguimientos-objetivo", response_model=SeguimientoObjetivoResponse, status_code=status.HTTP_201_CREATED)
def crear_seguimiento_objetivo(
    seguimiento: SeguimientoObjetivoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo seguimiento de objetivo"""
    # Verificar que el objetivo existe
    objetivo = db.query(ObjetivoCalidad).filter(ObjetivoCalidad.id == seguimiento.objetivo_calidad_id).first()
    if not objetivo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objetivo de calidad no encontrado"
        )
    
    nuevo_seguimiento = SeguimientoObjetivo(**seguimiento.model_dump())
    db.add(nuevo_seguimiento)
    db.commit()
    db.refresh(nuevo_seguimiento)
    
    # Opcional: Actualizar el progreso del objetivo automáticamente
    # Esto dependería de la lógica de negocio (si el seguimiento define el progreso)
    
    return nuevo_seguimiento


@router.put("/seguimientos-objetivo/{seguimiento_id}", response_model=SeguimientoObjetivoResponse)
def actualizar_seguimiento_objetivo(
    seguimiento_id: UUID,
    seguimiento_update: SeguimientoObjetivoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un seguimiento de objetivo"""
    seguimiento = db.query(SeguimientoObjetivo).filter(SeguimientoObjetivo.id == seguimiento_id).first()
    if not seguimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seguimiento no encontrado"
        )
    
    update_data = seguimiento_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(seguimiento, field, value)
    
    db.commit()
    db.refresh(seguimiento)
    return seguimiento


@router.delete("/seguimientos-objetivo/{seguimiento_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_seguimiento_objetivo(
    seguimiento_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un seguimiento de objetivo"""
    seguimiento = db.query(SeguimientoObjetivo).filter(SeguimientoObjetivo.id == seguimiento_id).first()
    if not seguimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seguimiento no encontrado"
        )
    
    db.delete(seguimiento)
    db.commit()
    return None
