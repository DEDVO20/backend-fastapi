"""
Endpoints CRUD para gestión de calidad
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.calidad import Indicador, NoConformidad, AccionCorrectiva, ObjetivoCalidad, SeguimientoObjetivo, AccionCorrectivaComentario
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
    AccionCorrectivaImplementacion,
    AccionCorrectivaComentarioCreate,
    AccionCorrectivaComentarioResponse,
    ObjetivoCalidadCreate,
    ObjetivoCalidadUpdate,

    ObjetivoCalidadResponse,
    SeguimientoObjetivoCreate,
    SeguimientoObjetivoUpdate,
    SeguimientoObjetivoResponse
)
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario, Area

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
    
    data = indicador.model_dump()
    if 'activo' in data and isinstance(data['activo'], bool):
        data['activo'] = 1 if data['activo'] else 0
    nuevo_indicador = Indicador(**data)
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
        # Convertir activo de bool a int (la columna es Integer, no Boolean)
        if field == 'activo' and isinstance(value, bool):
            value = 1 if value else 0
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
    
    no_conformidades = query.options(
        joinedload(NoConformidad.proceso),
        joinedload(NoConformidad.detector),
        joinedload(NoConformidad.responsable)
    ).offset(skip).limit(limit).all()
    return no_conformidades


@router.post("/no-conformidades", response_model=NoConformidadResponse, status_code=status.HTTP_201_CREATED)
def crear_no_conformidad(
    nc: NoConformidadCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva no conformidad"""
    # Verify permission "noconformidades.reportar"
    tiene_permiso = any(
        rp.permiso.codigo == "noconformidades.reportar" 
        for ur in current_user.roles 
        for rp in ur.rol.permisos
        if rp.permiso
    )
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
    
    # Recargar con relaciones
    nueva_nc = db.query(NoConformidad).options(
        joinedload(NoConformidad.proceso),
        joinedload(NoConformidad.detector),
        joinedload(NoConformidad.responsable)
    ).filter(NoConformidad.id == nueva_nc.id).first()
    
    return nueva_nc


@router.get("/no-conformidades/{nc_id}", response_model=NoConformidadResponse)
def obtener_no_conformidad(
    nc_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener una no conformidad por ID"""
    nc = db.query(NoConformidad).options(
        joinedload(NoConformidad.proceso),
        joinedload(NoConformidad.detector),
        joinedload(NoConformidad.responsable)
    ).filter(NoConformidad.id == nc_id).first()
    
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
    
    # Recargar con relaciones
    nc = db.query(NoConformidad).options(
        joinedload(NoConformidad.proceso),
        joinedload(NoConformidad.detector),
        joinedload(NoConformidad.responsable)
    ).filter(NoConformidad.id == nc_id).first()
    
    return nc


@router.delete("/no-conformidades/{nc_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_no_conformidad(
    nc_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar una no conformidad"""
    nc = db.query(NoConformidad).filter(NoConformidad.id == nc_id).first()
    if not nc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No conformidad no encontrada"
        )
    
    db.delete(nc)
    db.commit()
    return None


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
    query = db.query(AccionCorrectiva).options(
        joinedload(AccionCorrectiva.responsable),
        joinedload(AccionCorrectiva.implementador),
        joinedload(AccionCorrectiva.verificador),
        joinedload(AccionCorrectiva.comentarios).joinedload(AccionCorrectivaComentario.usuario)
    )
    
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
    accion = db.query(AccionCorrectiva).options(
        joinedload(AccionCorrectiva.responsable),
        joinedload(AccionCorrectiva.implementador),
        joinedload(AccionCorrectiva.verificador),
        joinedload(AccionCorrectiva.comentarios).joinedload(AccionCorrectivaComentario.usuario)
    ).filter(AccionCorrectiva.id == accion_id).first()
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


@router.patch("/acciones-correctivas/{accion_id}/implementar", response_model=AccionCorrectivaResponse)
def implementar_accion_correctiva(
    accion_id: UUID,
    implementacion: AccionCorrectivaImplementacion,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Implementar una acción correctiva"""
    accion = db.query(AccionCorrectiva).filter(AccionCorrectiva.id == accion_id).first()
    if not accion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acción correctiva no encontrada"
        )
    
    from datetime import date
    # Asignar quien implementó la acción
    accion.implementado_por = current_user.id
    
    # Si no se proporciona fecha de implementación, usar la fecha actual
    if implementacion.fechaImplementacion:
        accion.fecha_implementacion = implementacion.fechaImplementacion
    else:
        accion.fecha_implementacion = date.today()
    
    # Actualizar otros campos si se proporcionan
    if implementacion.observacion:
        accion.observacion = implementacion.observacion
    if implementacion.evidencias:
        accion.evidencias = implementacion.evidencias
    if implementacion.estado:
        accion.estado = implementacion.estado
    else:
        accion.estado = "implementada"
    
    db.commit()
    db.refresh(accion)
    
    # Cargar relaciones para la respuesta
    accion = db.query(AccionCorrectiva).options(
        joinedload(AccionCorrectiva.responsable),
        joinedload(AccionCorrectiva.implementador),
        joinedload(AccionCorrectiva.verificador),
        joinedload(AccionCorrectiva.comentarios).joinedload(AccionCorrectivaComentario.usuario)
    ).filter(AccionCorrectiva.id == accion_id).first()
    
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
    tiene_permiso = any(
        rp.permiso.codigo == "noconformidades.cerrar" 
        for ur in current_user.roles 
        for rp in ur.rol.permisos
        if rp.permiso
    )
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
    accion.verificado_por = current_user.id  # Asignar quien verificó
    
    if verificacion.observaciones:
        accion.observacion = verificacion.observaciones
    if verificacion.eficacia_verificada is not None:
        accion.eficacia_verificada = verificacion.eficacia_verificada
    
    # Cambiar estado a verificada
    accion.estado = "verificada"
    
    db.commit()
    db.refresh(accion)
    
    # Cargar relaciones para la respuesta
    accion = db.query(AccionCorrectiva).options(
        joinedload(AccionCorrectiva.responsable),
        joinedload(AccionCorrectiva.implementador),
        joinedload(AccionCorrectiva.verificador),
        joinedload(AccionCorrectiva.comentarios).joinedload(AccionCorrectivaComentario.usuario)
    ).filter(AccionCorrectiva.id == accion_id).first()
    
    return accion


from ..services.email import email_service

@router.post("/acciones-correctivas/{accion_id}/comentarios", response_model=AccionCorrectivaComentarioResponse)
async def crear_comentario_accion(
    accion_id: UUID,
    comentario: AccionCorrectivaComentarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Agregar un comentario a una acción correctiva"""
    # Verificar que la acción existe con sus responsables cargados
    accion = db.query(AccionCorrectiva).options(
        joinedload(AccionCorrectiva.responsable),
        joinedload(AccionCorrectiva.implementador),
        joinedload(AccionCorrectiva.verificador)
    ).filter(AccionCorrectiva.id == accion_id).first()
    
    if not accion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acción correctiva no encontrada"
        )
    
    nuevo_comentario = AccionCorrectivaComentario(
        accion_correctiva_id=accion_id,
        usuario_id=current_user.id,
        comentario=comentario.comentario
    )
    
    db.add(nuevo_comentario)
    db.commit()
    db.refresh(nuevo_comentario)
    
    # Notificar a los involucrados (background task idealmente, pero await aquí por simplicidad del stub)
    involucrados = []
    if accion.responsable: involucrados.append(accion.responsable)
    if accion.implementador: involucrados.append(accion.implementador)
    if accion.verificador: involucrados.append(accion.verificador)
    
    # Filtrar duplicados se hace en el servicio
    await email_service.notificar_nuevo_comentario(accion, current_user, comentario.comentario, involucrados)

    comentario_completo = db.query(AccionCorrectivaComentario).options(
        joinedload(AccionCorrectivaComentario.usuario)
    ).filter(AccionCorrectivaComentario.id == nuevo_comentario.id).first()
    
    return comentario_completo


@router.patch("/acciones-correctivas/{accion_id}/estado", response_model=AccionCorrectivaResponse)
def actualizar_estado_accion(
    accion_id: UUID,
    estado: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar manualmente el estado de una acción correctiva (ej. cerrar)"""
    # Verificar permisos (se podría refinar, por ahora cualquiera con acceso al modulo)
    
    accion = db.query(AccionCorrectiva).filter(AccionCorrectiva.id == accion_id).first()
    if not accion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acción correctiva no encontrada"
        )
    
    # Validar transiciones permitidas
    if estado == "cerrada" and accion.estado != "verificada":
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden cerrar acciones verificadas"
        )
        
    accion.estado = estado
    
    db.commit()
    db.refresh(accion)
    
    # Cargar relaciones
    accion = db.query(AccionCorrectiva).options(
        joinedload(AccionCorrectiva.responsable),
        joinedload(AccionCorrectiva.implementador),
        joinedload(AccionCorrectiva.verificador),
        joinedload(AccionCorrectiva.comentarios).joinedload(AccionCorrectivaComentario.usuario)
    ).filter(AccionCorrectiva.id == accion_id).first()

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
    query = db.query(ObjetivoCalidad).options(
        joinedload(ObjetivoCalidad.area),
        joinedload(ObjetivoCalidad.responsable)
    )
    
    if area_id:
        query = query.filter(ObjetivoCalidad.area_id == area_id)
    if estado:
        estados = [s.strip() for s in estado.split(",") if s.strip()]
        if len(estados) > 1:
            query = query.filter(ObjetivoCalidad.estado.in_(estados))
        elif len(estados) == 1:
            query = query.filter(ObjetivoCalidad.estado == estados[0])
    
    objetivos = query.offset(skip).limit(limit).all()
    
    # Auto-transición de estados según fechas
    from datetime import datetime, timezone
    ahora = datetime.now(timezone.utc)
    cambios = False
    for obj in objetivos:
        # Planificado → En curso: si la fecha de inicio ya pasó
        if obj.estado == 'planificado' and obj.fecha_inicio <= ahora:
            obj.estado = 'en_curso'
            cambios = True
        # En curso → No cumplido: si la fecha fin ya pasó y progreso < 100
        elif obj.estado == 'en_curso' and obj.fecha_fin <= ahora and (obj.progreso or 0) < 100:
            obj.estado = 'no_cumplido'
            cambios = True
    
    if cambios:
        db.commit()
    
    return objetivos


@router.post("/objetivos-calidad", response_model=ObjetivoCalidadResponse, status_code=status.HTTP_201_CREATED)
def crear_objetivo_calidad(
    objetivo: ObjetivoCalidadCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo objetivo de calidad"""
    codigo_normalizado = objetivo.codigo.strip().upper()

    if not objetivo.area_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El área es obligatoria para el objetivo de calidad"
        )

    if not objetivo.responsable_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El responsable es obligatorio para el objetivo de calidad"
        )

    area = db.query(Area).filter(Area.id == objetivo.area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El área seleccionada no existe"
        )

    responsable = db.query(Usuario).filter(Usuario.id == objetivo.responsable_id).first()
    if not responsable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El responsable seleccionado no existe"
        )

    # Verificar código único
    db_objetivo = db.query(ObjetivoCalidad).filter(ObjetivoCalidad.codigo == codigo_normalizado).first()
    if db_objetivo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de objetivo ya existe"
        )
    
    objetivo_data = objetivo.model_dump()
    objetivo_data["codigo"] = codigo_normalizado

    nuevo_objetivo = ObjetivoCalidad(**objetivo_data)
    db.add(nuevo_objetivo)
    db.commit()
    nuevo_objetivo = db.query(ObjetivoCalidad).options(
        joinedload(ObjetivoCalidad.area),
        joinedload(ObjetivoCalidad.responsable)
    ).filter(ObjetivoCalidad.id == nuevo_objetivo.id).first()
    return nuevo_objetivo


@router.get("/objetivos-calidad/{objetivo_id}", response_model=ObjetivoCalidadResponse)
def obtener_objetivo_calidad(
    objetivo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un objetivo de calidad por ID"""
    objetivo = db.query(ObjetivoCalidad).options(
        joinedload(ObjetivoCalidad.area),
        joinedload(ObjetivoCalidad.responsable)
    ).filter(ObjetivoCalidad.id == objetivo_id).first()
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

    fecha_inicio = update_data.get("fecha_inicio", objetivo.fecha_inicio)
    fecha_fin = update_data.get("fecha_fin", objetivo.fecha_fin)
    if fecha_fin <= fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )

    if "area_id" in update_data and update_data["area_id"]:
        area = db.query(Area).filter(Area.id == update_data["area_id"]).first()
        if not area:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El área seleccionada no existe"
            )

    if "responsable_id" in update_data and update_data["responsable_id"]:
        responsable = db.query(Usuario).filter(Usuario.id == update_data["responsable_id"]).first()
        if not responsable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El responsable seleccionado no existe"
            )

    if "codigo" in update_data and update_data["codigo"]:
        codigo_normalizado = update_data["codigo"].strip().upper()
        existe_codigo = db.query(ObjetivoCalidad).filter(
            ObjetivoCalidad.codigo == codigo_normalizado,
            ObjetivoCalidad.id != objetivo_id
        ).first()
        if existe_codigo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código de objetivo ya existe"
            )
        update_data["codigo"] = codigo_normalizado

    for field, value in update_data.items():
        setattr(objetivo, field, value)
    
    db.commit()
    objetivo = db.query(ObjetivoCalidad).options(
        joinedload(ObjetivoCalidad.area),
        joinedload(ObjetivoCalidad.responsable)
    ).filter(ObjetivoCalidad.id == objetivo_id).first()
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
    
    # Auto-actualizar progreso del objetivo si hay valor_meta y valor_actual
    if seguimiento.valor_actual is not None and objetivo.valor_meta and objetivo.valor_meta > 0:
        progreso = min((seguimiento.valor_actual / objetivo.valor_meta) * 100, 100)
        objetivo.progreso = progreso
        
        # Auto-marcar como cumplido si progreso >= 100%
        if progreso >= 100 and objetivo.estado not in ('cumplido', 'cancelado'):
            objetivo.estado = 'cumplido'
    
    # Auto-transición: si está "planificado" y la fecha de inicio ya pasó, cambiar a "en_curso"
    from datetime import datetime, timezone
    ahora = datetime.now(timezone.utc)
    if objetivo.estado == 'planificado' and objetivo.fecha_inicio <= ahora:
        objetivo.estado = 'en_curso'
    
    db.commit()
    db.refresh(nuevo_seguimiento)
    
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
