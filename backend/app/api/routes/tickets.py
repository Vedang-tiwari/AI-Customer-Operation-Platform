from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.ticket import Ticket
from app.models.message import Message
from app.models.organization import Organization
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketListResponse,
    TicketEscalateRequest
)
from app.schemas.message import MessageCreate, MessageResponse
from app.services.ticket_service import create_ticket, update_ticket_state, process_ticket_ai
from app.services.audit_service import record_audit_event
from app.api.dependencies import get_current_user, get_current_organization

router = APIRouter(prefix="/tickets", tags=["Tickets & Conversations"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_new_ticket(
    ticket_in: TicketCreate,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Create a ticket, check idempotency, and run AI classification & draft generation."""
    ticket = create_ticket(
        db=db,
        organization_id=org.id,
        ticket_in=ticket_in,
        actor_id=current_user.id,
        actor_email=current_user.email
    )
    return ticket


@router.get("", response_model=TicketListResponse)
def list_tickets(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    category_filter: Optional[str] = Query(None, alias="category"),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """List tickets for the current tenant organization with filtering."""
    query = select(Ticket).where(Ticket.organization_id == org.id)

    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if priority_filter:
        query = query.where(Ticket.priority == priority_filter)
    if category_filter:
        query = query.where(Ticket.category == category_filter)
    if search:
        query = query.where(Ticket.subject.ilike(f"%{search}%") | Ticket.description.ilike(f"%{search}%"))

    query = query.order_by(Ticket.created_at.desc())
    all_matching = db.scalars(query).all()
    total = len(all_matching)
    items = all_matching[offset:offset + limit]

    return TicketListResponse(total=total, items=items)


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: str,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Retrieve ticket details with tenant verification."""
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == org.id)
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Update ticket permitted fields with state transition validation."""
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == org.id)
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    updated = update_ticket_state(
        db=db,
        ticket=ticket,
        ticket_update=ticket_update,
        actor_id=current_user.id,
        actor_email=current_user.email
    )
    return updated


@router.get("/{ticket_id}/messages", response_model=List[MessageResponse])
def get_ticket_messages(
    ticket_id: str,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Retrieve conversation messages for a ticket."""
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == org.id)
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    messages = db.scalars(
        select(Message).where(Message.ticket_id == ticket.id).order_by(Message.created_at.asc())
    ).all()
    return messages


@router.post("/{ticket_id}/messages", response_model=MessageResponse)
def add_ticket_message(
    ticket_id: str,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Add a message or internal note to a ticket."""
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == org.id)
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    message = Message(
        ticket_id=ticket.id,
        sender_type=msg_in.sender_type,
        sender_id=current_user.id,
        sender_name=msg_in.sender_name or current_user.full_name,
        body=msg_in.body
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    record_audit_event(
        db=db,
        organization_id=org.id,
        action="ticket.message_added",
        target_type="ticket",
        target_id=ticket.id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details={"sender_type": msg_in.sender_type}
    )
    return message


@router.post("/{ticket_id}/classify", response_model=TicketResponse)
def trigger_ticket_classification(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Trigger AI classification and response draft generation on demand."""
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == org.id)
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    processed = process_ticket_ai(db, ticket)
    return processed


@router.post("/{ticket_id}/escalate", response_model=TicketResponse)
def escalate_ticket(
    ticket_id: str,
    esc_in: TicketEscalateRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Manually escalate a ticket to urgent priority and triage."""
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == org.id)
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    ticket.priority = esc_in.target_priority
    ticket.status = "needs_triage"
    db.commit()
    db.refresh(ticket)

    record_audit_event(
        db=db,
        organization_id=org.id,
        action="ticket.escalated",
        target_type="ticket",
        target_id=ticket.id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details={"reason": esc_in.reason, "priority": esc_in.target_priority}
    )
    return ticket
