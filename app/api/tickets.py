from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.ticket import Ticket, EstadoTicket
from ..models.usuario import Usuario
from ..schemas.ticket import TicketCreate, TicketUpdate, TicketResponse
from .auth import get_current_user
import uuid

router = APIRouter()

@router.post("/", response_model=TicketResponse)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
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
    query = db.query(Ticket)
    
    # Si no es admin, solo ve sus tickets (logica simplificada por ahora, asumiendo todos ven todo o filtro simple)
    # TODO: Implementar permisos mas granulares
    query = query.filter(Ticket.solicitante_id == current_user.id)
    
    if estado:
        query = query.filter(Ticket.estado == estado)
        
    tickets = query.offset(skip).limit(limit).all()
    return tickets

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Verificar acceso (solo solicitante o admin)
    if ticket.solicitante_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
         
    return ticket

@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: uuid.UUID,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Validaciones de permisos aqui...
    
    for key, value in ticket_update.dict(exclude_unset=True).items():
        if hasattr(ticket, key):
            # Handle Enums
            if hasattr(value, 'value'):
                 setattr(ticket, key, value.value)
            else:
                 setattr(ticket, key, value)
            
    db.commit()
    db.refresh(ticket)
    return ticket
