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
from ..schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketResolver
from .auth import get_current_user
from ..utils.notification_service import crear_notificacion_asignacion, crear_notificacion_ticket_resuelto
from datetime import datetime

router = APIRouter()


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo ticket"""
    # Validar que el área destino existe si se proporciona
    if ticket.area_destino_id:
        from ..models.usuario import Area
        area = db.query(Area).filter(Area.id == ticket.area_destino_id).first()
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área destino no encontrada"
            )
    
    new_ticket = Ticket(
        titulo=ticket.titulo,
        descripcion=ticket.descripcion,
        categoria=ticket.categoria,
        prioridad=ticket.prioridad,
        solicitante_id=current_user.id,
        area_destino_id=ticket.area_destino_id
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket


@router.get("/", response_model=List[TicketResponse])
def list_tickets(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar tickets según el rol y área del usuario"""
    from sqlalchemy import or_
    
    # Verificar si el usuario es admin o gestor de calidad
    es_admin_o_gestor = any(
        ur.rol.clave in ['admin', 'gestor_calidad'] 
        for ur in current_user.roles
    )
    
    # Construir query base
    query = db.query(Ticket)
    
    # Aplicar filtros de visibilidad según rol
    if not es_admin_o_gestor:
        # Usuarios regulares ven:
        # 1. Tickets que crearon
        # 2. Tickets asignados a su área
        # 3. Tickets asignados directamente a ellos
        query = query.filter(
            or_(
                Ticket.solicitante_id == current_user.id,
                Ticket.area_destino_id == current_user.area_id,
                Ticket.asignado_a == current_user.id
            )
        )
    # Si es admin/gestor, ve todos los tickets (no se aplica filtro adicional)
    
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
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un ticket por ID"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Verificar si el usuario es admin o gestor de calidad
    es_admin_o_gestor = any(
        ur.rol.clave in ['admin', 'gestor_calidad'] 
        for ur in current_user.roles
    )
    
    # Verificar acceso
    tiene_acceso = (
        ticket.solicitante_id == current_user.id or  # Es el solicitante
        ticket.asignado_a == current_user.id or      # Está asignado a él
        ticket.area_destino_id == current_user.area_id or  # Es de su área
        es_admin_o_gestor  # Es admin o gestor
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
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Verificar si cambió la asignación
    previous_asignado_a = ticket.asignado_a
    
    # Actualizar campos
    for key, value in ticket_update.model_dump(exclude_unset=True).items():
        if hasattr(ticket, key) and value is not None:
            setattr(ticket, key, value)
            
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
    current_user: Usuario = Depends(get_current_user)
):
    """Resolver un ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Verificar si el usuario es admin o gestor de calidad
    es_admin_o_gestor = any(
        ur.rol.clave in ['admin', 'gestor_calidad'] 
        for ur in current_user.roles
    )
    
    # REGLA: El solicitante NO puede resolver su propio ticket
    if ticket.solicitante_id == current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="No puedes resolver tu propio ticket"
        )
    
    # Verificar que el usuario puede resolver el ticket
    puede_resolver = (
        ticket.asignado_a == current_user.id or  # Está asignado a él
        ticket.area_destino_id == current_user.area_id or  # Es de su área
        es_admin_o_gestor  # Es admin o gestor
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
