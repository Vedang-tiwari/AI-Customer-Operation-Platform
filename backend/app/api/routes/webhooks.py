from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.organization import Organization
from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.ticket_service import create_ticket

router = APIRouter(prefix="/webhooks", tags=["External Webhooks"])


class WebhookTicketPayload(BaseModel):
    subject: str
    description: str
    event_id: str
    source_platform: Optional[str] = "webhook"


@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def receive_ticket_webhook(
    payload: WebhookTicketPayload,
    x_org_slug: Optional[str] = Header("default", alias="X-Org-Slug"),
    db: Session = Depends(get_db)
):
    """
    Ingests external webhook events into tickets with idempotency on event_id.
    """
    org = db.scalar(select(Organization).where(Organization.slug == x_org_slug))
    if not org:
        # Fallback to first org in system
        org = db.scalar(select(Organization))
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant organization not configured")

    ticket_in = TicketCreate(
        subject=payload.subject,
        description=payload.description,
        source=payload.source_platform or "webhook",
        external_id=payload.event_id,
        idempotency_key=f"webhook-{payload.event_id}"
    )

    ticket = create_ticket(
        db=db,
        organization_id=org.id,
        ticket_in=ticket_in,
        actor_id=None,
        actor_email="webhook-system"
    )
    return ticket
