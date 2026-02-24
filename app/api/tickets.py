"""
API endpoints para Tickets
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.ticket import Ticket, EstadoTicket
from ..models.usuario import Usuario
from ..schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketResolver, TicketDecision
from ..api.dependencies import require_any_permission
from ..utils.notification_service import (
    crear_notificacion_asignacion,
    crear_notificacion_ticket_resuelto,
    crear_notificacion_resultado_solicitud,
)
from datetime import datetime

router = APIRouter()

def _inferir_prioridad(categoria: str, titulo: str, descripcion: str) -> str:
    """
    Prioridad automática basada en tipo de solicitud y señales de urgencia.
    """
    texto = f"{titulo} {descripcion}".lower()

    # Reglas por categoría
    prioridad_base = {
        "soporte": "alta",
        "consulta": "baja",
        "mejora": "media",
        "solicitud_documento": "media",
    }.get(categoria, "media")

    # Escala por términos críticos
    palabras_criticas = [
        "caido", "caída", "bloquea", "bloqueado", "produccion",
        "producción", "urgente", "no funciona", "inoperante",
    ]
    if any(p in texto for p in palabras_criticas):
        return "critica"

    palabras_altas = ["error", "falla", "incidente", "no puedo", "fallo"]
    if any(p in texto for p in palabras_altas):
        return "alta" if prioridad_base in {"baja", "media"} else prioridad_base

    return prioridad_base


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.ver","documentos.crear","documentos.revisar","documentos.aprobar","documentos.anular","calidad.ver","auditorias.ver","auditorias.planificar","auditorias.ejecutar","riesgos.identificar","riesgos.ver","riesgos.gestion","capacitaciones.gestion","usuarios.ver","usuarios.gestion","noconformidades.reportar","noconformidades.gestion","noconformidades.cerrar","procesos.admin","sistema.config","sistema.admin"]))
):
    """Crear un nuevo ticket"""
    if not ticket.area_destino_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe seleccionar un área destino para crear el ticket"
        )

    # Validar que el área destino existe si se proporciona
    from ..models.usuario import Area
    from ..models.sistema import Asignacion
    area = db.query(Area).filter(Area.id == ticket.area_destino_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área destino no encontrada"
        )
    
    # Validar documento público si se proporciona
    if ticket.documento_publico_id:
        from ..models.documento import Documento
        documento = db.query(Documento).filter(Documento.id == ticket.documento_publico_id).first()
        if not documento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento público no encontrado"
            )
    
    asignado_a = None
    principal = db.query(Asignacion).filter(
        Asignacion.area_id == ticket.area_destino_id,
        Asignacion.es_principal == True
    ).first()
    if principal:
        asignado_a = principal.usuario_id
    else:
        alterno = db.query(Asignacion).filter(
            Asignacion.area_id == ticket.area_destino_id
        ).first()
        if alterno:
            asignado_a = alterno.usuario_id

    if not asignado_a:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El area seleccionada no tiene responsable de tickets asignado"
        )

    prioridad_calculada = _inferir_prioridad(
        ticket.categoria or "soporte",
        ticket.titulo or "",
        ticket.descripcion or "",
    )

    new_ticket = Ticket(
        titulo=ticket.titulo,
        descripcion=ticket.descripcion,
        categoria=ticket.categoria,
        prioridad=prioridad_calculada,
        solicitante_id=current_user.id,
        area_destino_id=ticket.area_destino_id,
        asignado_a=asignado_a,
        documento_publico_id=ticket.documento_publico_id,
        archivo_adjunto_url=ticket.archivo_adjunto_url,
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    # Notificar al responsable de área cuando aplica
    if asignado_a:
        crear_notificacion_asignacion(
            db=db,
            usuario_id=asignado_a,
            titulo="Nueva solicitud de documento",
            mensaje=f"Se ha creado una solicitud pendiente para: {new_ticket.titulo}",
            referencia_tipo="ticket",
            referencia_id=new_ticket.id
        )
    return new_ticket


@router.get("/", response_model=List[TicketResponse])
def list_tickets(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.ver","documentos.crear","documentos.revisar","documentos.aprobar","documentos.anular","calidad.ver","auditorias.ver","auditorias.planificar","auditorias.ejecutar","riesgos.identificar","riesgos.ver","riesgos.gestion","capacitaciones.gestion","usuarios.ver","usuarios.gestion","noconformidades.reportar","noconformidades.gestion","noconformidades.cerrar","procesos.admin","sistema.config","sistema.admin"]))
):
    """Listar tickets según el rol y área del usuario"""
    from sqlalchemy import or_
    from sqlalchemy.orm import joinedload
    
    # Construir query base con eager loading de relaciones
    query = db.query(Ticket).options(
        joinedload(Ticket.solicitante),
        joinedload(Ticket.asignado)
    )
    
    # Visibilidad estricta por área:
    # 1) los que crea el usuario
    # 2) los de su área
    # 3) los asignados directamente al usuario
    if current_user.area_id:
        query = query.filter(
            or_(
                Ticket.solicitante_id == current_user.id,
                Ticket.area_destino_id == current_user.area_id,
                Ticket.asignado_a == current_user.id
            )
        )
    else:
        query = query.filter(
            or_(
                Ticket.solicitante_id == current_user.id,
                Ticket.asignado_a == current_user.id
            )
        )
    
    # Filtro por estado si se proporciona
    if estado:
        query = query.filter(Ticket.estado == estado)
    
    # Ordenar por fecha de creación descendente
    query = query.order_by(Ticket.creado_en.desc())
    
    tickets = query.offset(skip).limit(limit).all()
    return tickets


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.ver","documentos.crear","documentos.revisar","documentos.aprobar","documentos.anular","calidad.ver","auditorias.ver","auditorias.planificar","auditorias.ejecutar","riesgos.identificar","riesgos.ver","riesgos.gestion","capacitaciones.gestion","usuarios.ver","usuarios.gestion","noconformidades.reportar","noconformidades.gestion","noconformidades.cerrar","procesos.admin","sistema.config","sistema.admin"]))
):
    """Obtener un ticket por ID"""
    from sqlalchemy.orm import joinedload
    
    ticket = db.query(Ticket).options(
        joinedload(Ticket.solicitante),
        joinedload(Ticket.asignado)
    ).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Verificar acceso estricto por área
    tiene_acceso = (
        ticket.solicitante_id == current_user.id or  # Es el solicitante
        ticket.asignado_a == current_user.id or      # Está asignado a él
        ticket.area_destino_id == current_user.area_id  # Es de su área
    )
    
    if not tiene_acceso:
        raise HTTPException(
            status_code=403, 
            detail="No autorizado para ver este ticket"
        )
    
    return ticket


@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: UUID,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.ver","documentos.crear","documentos.revisar","documentos.aprobar","documentos.anular","calidad.ver","auditorias.ver","auditorias.planificar","auditorias.ejecutar","riesgos.identificar","riesgos.ver","riesgos.gestion","capacitaciones.gestion","usuarios.ver","usuarios.gestion","noconformidades.reportar","noconformidades.gestion","noconformidades.cerrar","procesos.admin","sistema.config","sistema.admin"]))
):
    """Actualizar un ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Verificar si cambió la asignación
    previous_asignado_a = ticket.asignado_a
    
    payload = ticket_update.model_dump(exclude_unset=True)

    # Actualizar campos (excepto prioridad, se calcula automáticamente)
    payload.pop("prioridad", None)

    for key, value in payload.items():
        if hasattr(ticket, key) and value is not None:
            setattr(ticket, key, value)

    # Recalcular prioridad si cambió información relevante
    if any(k in payload for k in ["categoria", "titulo", "descripcion"]):
        ticket.prioridad = _inferir_prioridad(
            ticket.categoria or "soporte",
            ticket.titulo or "",
            ticket.descripcion or "",
        )
            
    db.commit()
    db.refresh(ticket)
    
    # Enviar notificación si hubo nueva asignación
    if ticket.asignado_a and ticket.asignado_a != previous_asignado_a:
        crear_notificacion_asignacion(
            db=db,
            usuario_id=ticket.asignado_a,
            titulo="Nuevo Ticket Asignado",
            mensaje=f"Se te ha asignado el ticket: {ticket.titulo}",
            referencia_tipo="ticket",
            referencia_id=ticket.id
        )
        
    return ticket


@router.post("/{ticket_id}/resolver", response_model=TicketResponse)
def resolver_ticket(
    ticket_id: UUID,
    resolucion: TicketResolver,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.ver","documentos.crear","documentos.revisar","documentos.aprobar","documentos.anular","calidad.ver","auditorias.ver","auditorias.planificar","auditorias.ejecutar","riesgos.identificar","riesgos.ver","riesgos.gestion","capacitaciones.gestion","usuarios.ver","usuarios.gestion","noconformidades.reportar","noconformidades.gestion","noconformidades.cerrar","procesos.admin","sistema.config","sistema.admin"]))
):
    """Resolver un ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # REGLA: El solicitante NO puede resolver su propio ticket
    if ticket.solicitante_id == current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="No puedes resolver tu propio ticket"
        )
    
    # Verificar que el usuario puede resolver el ticket
    puede_resolver = (
        ticket.asignado_a == current_user.id or  # Está asignado a él
        ticket.area_destino_id == current_user.area_id  # Es de su área
    )
    
    if not puede_resolver:
        raise HTTPException(
            status_code=403, 
            detail="No tienes permiso para resolver este ticket"
        )
    
    # Actualizar estado y solución
    ticket.estado = "resuelto"
    ticket.solucion = resolucion.solucion
    ticket.fecha_resolucion = datetime.now()
    if resolucion.satisfaccion_cliente:
        ticket.satisfaccion_cliente = resolucion.satisfaccion_cliente
            
    db.commit()
    db.refresh(ticket)
    
    # Notificar al solicitante
    crear_notificacion_ticket_resuelto(
        db=db,
        usuario_id=ticket.solicitante_id,
        titulo_ticket=ticket.titulo,
        referencia_id=ticket.id
    )
    
    return ticket


@router.post("/{ticket_id}/aprobar", response_model=TicketResponse)
def aprobar_ticket(
    ticket_id: UUID,
    decision: TicketDecision,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.ver","documentos.crear","documentos.revisar","documentos.aprobar","documentos.anular","calidad.ver","auditorias.ver","auditorias.planificar","auditorias.ejecutar","riesgos.identificar","riesgos.ver","riesgos.gestion","capacitaciones.gestion","usuarios.ver","usuarios.gestion","noconformidades.reportar","noconformidades.gestion","noconformidades.cerrar","procesos.admin","sistema.config","sistema.admin"]))
):
    """Aprobar solicitud de ticket (flujo de documentos públicos)"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    puede_decidir = (
        ticket.asignado_a == current_user.id
    )

    if not puede_decidir:
        raise HTTPException(status_code=403, detail="No tienes permiso para aprobar esta solicitud")

    ticket.estado = EstadoTicket.APROBADO.value
    ticket.solucion = decision.comentario or "Solicitud aprobada"
    ticket.fecha_resolucion = datetime.now()
    db.commit()
    db.refresh(ticket)

    crear_notificacion_resultado_solicitud(
        db=db,
        usuario_id=ticket.solicitante_id,
        titulo_ticket=ticket.titulo,
        estado=EstadoTicket.APROBADO.value,
        referencia_id=ticket.id,
        comentario=decision.comentario,
    )
    return ticket


@router.post("/{ticket_id}/declinar", response_model=TicketResponse)
def declinar_ticket(
    ticket_id: UUID,
    decision: TicketDecision,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.ver","documentos.crear","documentos.revisar","documentos.aprobar","documentos.anular","calidad.ver","auditorias.ver","auditorias.planificar","auditorias.ejecutar","riesgos.identificar","riesgos.ver","riesgos.gestion","capacitaciones.gestion","usuarios.ver","usuarios.gestion","noconformidades.reportar","noconformidades.gestion","noconformidades.cerrar","procesos.admin","sistema.config","sistema.admin"]))
):
    """Declinar solicitud de ticket (flujo de documentos públicos)"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    puede_decidir = (
        ticket.asignado_a == current_user.id
    )

    if not puede_decidir:
        raise HTTPException(status_code=403, detail="No tienes permiso para declinar esta solicitud")

    ticket.estado = EstadoTicket.DECLINADO.value
    ticket.solucion = decision.comentario or "Solicitud declinada"
    ticket.fecha_resolucion = datetime.now()
    db.commit()
    db.refresh(ticket)

    crear_notificacion_resultado_solicitud(
        db=db,
        usuario_id=ticket.solicitante_id,
        titulo_ticket=ticket.titulo,
        estado=EstadoTicket.DECLINADO.value,
        referencia_id=ticket.id,
        comentario=decision.comentario,
    )
    return ticket
