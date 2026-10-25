from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.draft import ResponseDraft
from app.models.ticket import Ticket
from app.schemas.draft import DraftUpdate, DraftReject
from app.services.audit_service import record_audit_event


def edit_draft(
    db: Session,
    draft_id: str,
    draft_in: DraftUpdate,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None
) -> ResponseDraft:
    draft = db.get(ResponseDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    draft.body = draft_in.body
    db.commit()
    db.refresh(draft)

    record_audit_event(
        db=db,
        organization_id=draft.ticket.organization_id,
        action="draft.edited",
        target_type="draft",
        target_id=draft.id,
        actor_id=actor_id,
        actor_email=actor_email,
        details={"body_length": len(draft.body)}
    )
    return draft


def approve_draft(
    db: Session,
    draft_id: str,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None
) -> ResponseDraft:
    draft = db.get(ResponseDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    draft.status = "approved"
    draft.reviewed_by_id = actor_id
    draft.reviewed_at = datetime.now(timezone.utc)
    
    # Update parent ticket state
    ticket = draft.ticket
    ticket.status = "approved"

    db.commit()
    db.refresh(draft)

    record_audit_event(
        db=db,
        organization_id=ticket.organization_id,
        action="draft.approved",
        target_type="draft",
        target_id=draft.id,
        actor_id=actor_id,
        actor_email=actor_email,
        details={"ticket_id": ticket.id}
    )
    return draft


def reject_draft(
    db: Session,
    draft_id: str,
    reject_in: DraftReject,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None
) -> ResponseDraft:
    draft = db.get(ResponseDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    draft.status = "rejected"
    draft.rejection_reason = reject_in.reason
    draft.reviewed_by_id = actor_id
    draft.reviewed_at = datetime.now(timezone.utc)

    ticket = draft.ticket
    ticket.status = "needs_triage"

    db.commit()
    db.refresh(draft)

    record_audit_event(
        db=db,
        organization_id=ticket.organization_id,
        action="draft.rejected",
        target_type="draft",
        target_id=draft.id,
        actor_id=actor_id,
        actor_email=actor_email,
        details={"reason": reject_in.reason, "ticket_id": ticket.id}
    )
    return draft
