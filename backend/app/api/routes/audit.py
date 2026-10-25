from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.audit import AuditEvent
from app.models.organization import Organization
from app.schemas.audit import AuditEventListResponse
from app.api.dependencies import get_current_organization

router = APIRouter(prefix="/audit-events", tags=["Audit & Compliance"])


@router.get("", response_model=AuditEventListResponse)
def list_audit_events(
    action: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Retrieve immutable audit events for the current organization."""
    query = select(AuditEvent).where(AuditEvent.organization_id == org.id)
    if action:
        query = query.where(AuditEvent.action == action)
    if target_type:
        query = query.where(AuditEvent.target_type == target_type)

    query = query.order_by(AuditEvent.timestamp.desc())
    all_events = db.scalars(query).all()
    total = len(all_events)
    items = all_events[offset:offset + limit]

    return AuditEventListResponse(total=total, items=items)
