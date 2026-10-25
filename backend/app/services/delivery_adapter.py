from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.draft import ResponseDraft
from app.models.message import Message
from app.models.ticket import Ticket
from app.services.audit_service import record_audit_event
from app.core.logging import logger


class DeliveryResult:
    def __init__(self, success: bool, message: str, delivery_id: str):
        self.success = success
        self.message = message
        self.delivery_id = delivery_id


def deliver_approved_draft(
    db: Session,
    draft_id: str,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delivers an approved draft response to the customer via the authorized channel adapter.
    Prevents rejected or unapproved drafts from being dispatched.
    """
    draft = db.get(ResponseDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    if draft.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot deliver response: Draft status is '{draft.status}'. Human approval is required."
        )

    ticket = draft.ticket
    ticket.status = "sending"
    db.commit()

    try:
        # Simulate authorized external delivery (Email/Webhook/CRM adapter)
        delivery_reference = f"deliv-{draft.id[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
        logger.info(f"Delivering approved draft {draft.id} to ticket {ticket.id} via adapter [{delivery_reference}]")

        # 1. Post approved response into ticket conversation history as customer-facing message
        outgoing_msg = Message(
            ticket_id=ticket.id,
            sender_type="agent",
            sender_id=actor_id,
            sender_name=actor_email or "Customer Support Agent",
            body=draft.body
        )
        db.add(outgoing_msg)

        # 2. Transition ticket to 'sent'
        ticket.status = "sent"
        db.commit()
        db.refresh(ticket)

        # 3. Log delivery audit record
        record_audit_event(
            db=db,
            organization_id=ticket.organization_id,
            action="draft.delivered",
            target_type="draft",
            target_id=draft.id,
            actor_id=actor_id,
            actor_email=actor_email,
            details={
                "delivery_reference": delivery_reference,
                "ticket_id": ticket.id,
                "recipient_source": ticket.source
            }
        )

        return {
            "success": True,
            "ticket_id": ticket.id,
            "draft_id": draft.id,
            "delivery_status": "delivered",
            "message": "Response delivered successfully to customer."
        }

    except Exception as e:
        ticket.status = "send_failed"
        db.commit()
        logger.error(f"Failed to deliver draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"External delivery adapter failed: {str(e)}"
        )
