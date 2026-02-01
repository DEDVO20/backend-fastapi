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
from ..schemas.ticket import TicketCreate, TicketUpdate, TicketResponse
from .auth import get_current_user

router = APIRouter()


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo ticket"""
    new_ticket = Ticket(
        titulo=ticket.titulo,
        descripcion=ticket.descripcion,
        categoria=ticket.tipo,  # Mapear 'tipo' del frontend a 'categoria' en BD
        prioridad=ticket.prioridad,
        solicitante_id=current_user.id
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    # Convertir categoria a tipo para la respuesta
    return TicketResponse(
        id=new_ticket.id,
        titulo=new_ticket.titulo,
        descripcion=new_ticket.descripcion,
        tipo=new_ticket.categoria,  # Mapear 'categoria' de BD a 'tipo' para frontend
        prioridad=new_ticket.prioridad,
        estado=new_ticket.estado,
        solicitante_id=new_ticket.solicitante_id,
        asignado_a=new_ticket.asignado_a,
        creado_en=new_ticket.creado_en,
        actualizado_en=new_ticket.actualizado_en
    )


@router.get("/", response_model=List[TicketResponse])
def list_tickets(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar tickets del usuario actual"""
    query = db.query(Ticket).filter(Ticket.solicitante_id == current_user.id)
    
    if estado:
        query = query.filter(Ticket.estado == estado)
        
    tickets = query.offset(skip).limit(limit).all()
    
    # Convertir categoria a tipo para cada ticket
    return [
        TicketResponse(
            id=t.id,
            titulo=t.titulo,
            descripcion=t.descripcion,
            tipo=t.categoria,  # Mapear categoria de BD a tipo para frontend
            prioridad=t.prioridad,
            estado=t.estado,
            solicitante_id=t.solicitante_id,
            asignado_a=t.asignado_a,
            creado_en=t.creado_en,
            actualizado_en=t.actualizado_en
        )
        for t in tickets
    ]


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
    
    # Verificar acceso
    if ticket.solicitante_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este ticket")
    
    # Convertir categoria a tipo
    return TicketResponse(
        id=ticket.id,
        titulo=ticket.titulo,
        descripcion=ticket.descripcion,
        tipo=ticket.categoria,
        prioridad=ticket.prioridad,
        estado=ticket.estado,
        solicitante_id=ticket.solicitante_id,
        asignado_a=ticket.asignado_a,
        creado_en=ticket.creado_en,
        actualizado_en=ticket.actualizado_en
    )


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
    
    # Actualizar campos
    update_data = ticket_update.model_dump(exclude_unset=True)
    
    # Mapear 'tipo' a 'categoria' si está presente
    if 'tipo' in update_data:
        update_data['categoria'] = update_data.pop('tipo')
    
    for key, value in update_data.items():
        if hasattr(ticket, key) and value is not None:
            setattr(ticket, key, value)
            
    db.commit()
    db.refresh(ticket)
    
    # Convertir categoria a tipo para la respuesta
    return TicketResponse(
        id=ticket.id,
        titulo=ticket.titulo,
        descripcion=ticket.descripcion,
        tipo=ticket.categoria,
        prioridad=ticket.prioridad,
        estado=ticket.estado,
        solicitante_id=ticket.solicitante_id,
        asignado_a=ticket.asignado_a,
        creado_en=ticket.creado_en,
        actualizado_en=ticket.actualizado_en
    )
