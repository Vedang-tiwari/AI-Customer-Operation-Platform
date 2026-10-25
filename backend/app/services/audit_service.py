from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent
from app.core.logging import logger


def record_audit_event(
    db: Session,
    organization_id: str,
    action: str,
    target_type: str,
    target_id: str,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    """
    Creates an immutable audit record for operational tracking and compliance.
    """
    event = AuditEvent(
        organization_id=organization_id,
        actor_id=actor_id,
        actor_email=actor_email,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {}
    )
    db.add(event)
    try:
        db.commit()
        db.refresh(event)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist audit event: {e}")
        raise e
    return event
