from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.team import Team
from app.models.ticket import Ticket
from app.core.logging import logger


CATEGORY_TEAM_MAP = {
    "billing": ["Billing", "Billing Support", "Finance"],
    "technical": ["Technical Support", "Tech Support", "Engineering"],
    "security": ["Security", "Security & Compliance"],
    "account": ["Customer Care", "General", "Support"],
    "general": ["General", "Tier 1 Support", "Customer Care"]
}


def evaluate_escalation(
    category: Optional[str],
    priority: str,
    sentiment: Optional[str],
    content: str
) -> Tuple[str, bool, Optional[str]]:
    """
    Evaluates whether a ticket requires priority escalation and manual triage.
    Returns: (new_priority, needs_triage, escalation_reason)
    """
    lower_content = content.lower()
    
    # Security trigger -> immediate urgent priority & triage
    if category == "security" or any(k in lower_content for k in ["breach", "vulnerability", "unauthorized access", "compromised", "exploit"]):
        return "urgent", True, "Mandatory escalation: Security or data protection incident detected"

    # Extreme frustration escalation
    if sentiment in ["frustrated", "negative"] and priority in ["normal", "low"]:
        return "high", False, "Escalated to high priority due to customer frustration"

    # Severe system outage or payment block keywords
    if any(k in lower_content for k in ["outage", "system down", "cannot process payments", "production broken"]):
        return "urgent", True, "Escalated to urgent: Critical service outage keywords identified"

    return priority, False, None


def resolve_team_for_ticket(
    db: Session,
    organization_id: str,
    category: Optional[str]
) -> Optional[Team]:
    """
    Deterministically matches the ticket's category to an available team in the organization.
    """
    if not category:
        # Default to General team if available
        return db.scalar(
            select(Team).where(Team.organization_id == organization_id, Team.name.ilike("%general%"))
        )

    target_names = CATEGORY_TEAM_MAP.get(category.lower(), ["General"])
    for name in target_names:
        team = db.scalar(
            select(Team).where(
                Team.organization_id == organization_id,
                Team.name.ilike(f"%{name}%")
            )
        )
        if team:
            return team

    # Fallback to any first team in the organization
    return db.scalar(
        select(Team).where(Team.organization_id == organization_id)
    )
