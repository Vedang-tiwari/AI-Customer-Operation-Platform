from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.ticket import Ticket
from app.models.draft import ResponseDraft
from app.models.organization import Organization
from app.models.user import User
from app.schemas.draft import (
    DraftResponse,
    DraftUpdate,
    DraftReject,
    DraftSendResponse
)
from app.services.approval_service import edit_draft, approve_draft, reject_draft
from app.services.delivery_adapter import deliver_approved_draft
from app.services.ticket_service import process_ticket_ai
from app.api.dependencies import get_current_user, get_current_organization

router = APIRouter(tags=["AI Suggestions & Human Approval"])


@router.post("/tickets/{ticket_id}/drafts", response_model=DraftResponse)
def generate_ticket_draft(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Generate a new grounded response draft suggestion for a ticket."""
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == org.id)
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    process_ticket_ai(db, ticket)
    latest_draft = db.scalar(
        select(ResponseDraft)
        .where(ResponseDraft.ticket_id == ticket.id)
        .order_by(ResponseDraft.created_at.desc())
    )
    return latest_draft


@router.get("/tickets/{ticket_id}/drafts", response_model=List[DraftResponse])
def list_ticket_drafts(
    ticket_id: str,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """List all generated drafts and citations for a ticket."""
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == org.id)
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    drafts = db.scalars(
        select(ResponseDraft)
        .where(ResponseDraft.ticket_id == ticket.id)
        .order_by(ResponseDraft.created_at.desc())
    ).all()
    return drafts


@router.patch("/drafts/{draft_id}", response_model=DraftResponse)
def update_draft_body(
    draft_id: str,
    draft_in: DraftUpdate,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Edit draft text before approval."""
    draft = db.get(ResponseDraft, draft_id)
    if not draft or draft.ticket.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    return edit_draft(
        db=db,
        draft_id=draft_id,
        draft_in=draft_in,
        actor_id=current_user.id,
        actor_email=current_user.email
    )


@router.post("/drafts/{draft_id}/approve", response_model=DraftResponse)
def approve_response_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Approve an AI-generated draft response."""
    draft = db.get(ResponseDraft, draft_id)
    if not draft or draft.ticket.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    return approve_draft(
        db=db,
        draft_id=draft_id,
        actor_id=current_user.id,
        actor_email=current_user.email
    )


@router.post("/drafts/{draft_id}/reject", response_model=DraftResponse)
def reject_response_draft(
    draft_id: str,
    reject_in: DraftReject,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Reject an AI-generated draft response."""
    draft = db.get(ResponseDraft, draft_id)
    if not draft or draft.ticket.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    return reject_draft(
        db=db,
        draft_id=draft_id,
        reject_in=reject_in,
        actor_id=current_user.id,
        actor_email=current_user.email
    )


@router.post("/drafts/{draft_id}/send", response_model=DraftSendResponse)
def send_approved_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Deliver an approved draft response through the authorized adapter."""
    draft = db.get(ResponseDraft, draft_id)
    if not draft or draft.ticket.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    result = deliver_approved_draft(
        db=db,
        draft_id=draft_id,
        actor_id=current_user.id,
        actor_email=current_user.email
    )
    return result
