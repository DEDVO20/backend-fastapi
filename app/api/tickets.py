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
        tipo=ticket.tipo.value,
        prioridad=ticket.prioridad.value,
        solicitante_id=current_user.id
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
    """Listar tickets del usuario actual"""
    query = db.query(Ticket).filter(Ticket.solicitante_id == current_user.id)
    
    if estado:
        query = query.filter(Ticket.estado == estado)
        
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
    
    # Verificar acceso
    if ticket.solicitante_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este ticket")
          
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
        
    # Actualizar campos
    for key, value in ticket_update.model_dump(exclude_unset=True).items():
        if hasattr(ticket, key):
            # Manejar Enums
            if hasattr(value, 'value'):
                setattr(ticket, key, value.value)
            else:
                setattr(ticket, key, value)
            
    db.commit()
    db.refresh(ticket)
    return ticket
