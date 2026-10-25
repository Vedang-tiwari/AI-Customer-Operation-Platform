from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.ticket import Ticket
from app.models.message import Message
from app.models.draft import ResponseDraft, Citation
from app.models.job import ProcessingJob
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.routing_service import evaluate_escalation, resolve_team_for_ticket
from app.services.audit_service import record_audit_event
from app.ai.classifier import classify_ticket
from app.ai.retriever import retrieve_relevant_chunks
from app.ai.generator import generate_grounded_draft
from app.core.logging import logger


ALLOWED_TRANSITIONS = {
    "received": ["processing", "needs_triage", "awaiting_review", "resolved"],
    "processing": ["needs_triage", "awaiting_review", "resolved"],
    "needs_triage": ["processing", "awaiting_review", "approved", "resolved"],
    "awaiting_review": ["approved", "needs_triage", "resolved"],
    "approved": ["sending", "awaiting_review", "resolved"],
    "sending": ["sent", "send_failed"],
    "send_failed": ["approved", "needs_triage", "resolved"],
    "sent": ["resolved", "received"],
    "resolved": ["received", "processing"]  # Allow reopening
}


def validate_state_transition(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    return next_status in allowed


def create_ticket(
    db: Session,
    organization_id: str,
    ticket_in: TicketCreate,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None
) -> Ticket:
    """
    Creates a ticket with idempotency protection and executes initial processing.
    """
    # 1. Idempotency Check
    if ticket_in.idempotency_key:
        existing = db.scalar(
            select(Ticket).where(
                Ticket.organization_id == organization_id,
                Ticket.idempotency_key == ticket_in.idempotency_key
            )
        )
        if existing:
            logger.info(f"Idempotent ticket hit for key {ticket_in.idempotency_key}")
            return existing

    # 2. Instantiate Ticket
    ticket = Ticket(
        organization_id=organization_id,
        subject=ticket_in.subject,
        description=ticket_in.description,
        source=ticket_in.source,
        external_id=ticket_in.external_id,
        idempotency_key=ticket_in.idempotency_key,
        status="received",
        priority="normal",
        needs_human_review=True
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Add initial customer message to thread
    init_message = Message(
        ticket_id=ticket.id,
        sender_type="customer",
        sender_name="Customer",
        body=ticket.description
    )
    db.add(init_message)
    db.commit()

    record_audit_event(
        db=db,
        organization_id=organization_id,
        action="ticket.created",
        target_type="ticket",
        target_id=ticket.id,
        actor_id=actor_id,
        actor_email=actor_email,
        details={"subject": ticket.subject, "source": ticket.source}
    )

    # 3. Process AI Classification & Grounded Draft Generation
    process_ticket_ai(db, ticket)

    db.refresh(ticket)
    return ticket


def process_ticket_ai(db: Session, ticket: Ticket) -> Ticket:
    """
    Executes AI classification, routing, retrieval, and response draft generation.
    """
    ticket.status = "processing"
    db.commit()

    # Track processing job
    job = ProcessingJob(
        ticket_id=ticket.id,
        job_type="classify_and_draft",
        status="running",
        started_at=datetime.now(timezone.utc)
    )
    db.add(job)
    db.commit()

    try:
        # A. Classification
        cls_result = classify_ticket(ticket.subject, ticket.description)
        ticket.category = cls_result.category
        ticket.sentiment = cls_result.sentiment
        ticket.intent = cls_result.intent
        ticket.confidence_score = cls_result.confidence

        # B. Escalation & Priority Evaluation
        new_priority, needs_triage, esc_reason = evaluate_escalation(
            category=cls_result.category,
            priority=cls_result.priority,
            sentiment=cls_result.sentiment,
            content=f"{ticket.subject} {ticket.description}"
        )
        ticket.priority = new_priority

        # C. Team Routing
        matched_team = resolve_team_for_ticket(db, ticket.organization_id, ticket.category)
        if matched_team:
            ticket.assigned_team_id = matched_team.id

        # D. Grounded Knowledge Retrieval (Strictly Scoped by Organization)
        query = f"{ticket.subject} {ticket.description}"
        retrieved_chunks = retrieve_relevant_chunks(
            db=db,
            organization_id=ticket.organization_id,
            query=query,
            top_k=3
        )

        # E. Grounded Response Draft Generation & Citation Validation
        draft_body, validated_citations, draft_conf, model_name = generate_grounded_draft(
            subject=ticket.subject,
            description=ticket.description,
            retrieved_chunks=retrieved_chunks
        )

        draft = ResponseDraft(
            ticket_id=ticket.id,
            body=draft_body,
            status="draft",
            created_by_model=model_name,
            confidence_score=draft_conf
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        # Link validated citations
        for cit in validated_citations:
            citation_entry = Citation(
                draft_id=draft.id,
                chunk_id=cit["chunk_id"],
                passage_snippet=cit.get("passage_snippet"),
                relevance_score=cit.get("relevance_score")
            )
            db.add(citation_entry)

        # Update Ticket Lifecycle State
        if needs_triage or not retrieved_chunks:
            ticket.status = "needs_triage"
        else:
            ticket.status = "awaiting_review"

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(ticket)

    except Exception as e:
        logger.error(f"Error processing ticket AI: {e}")
        ticket.status = "needs_triage"
        job.status = "failed"
        job.error_code = "AI_PIPELINE_ERROR"
        job.error_message = str(e)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    return ticket


def update_ticket_state(
    db: Session,
    ticket: Ticket,
    ticket_update: TicketUpdate,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None
) -> Ticket:
    """
    Updates permitted ticket fields while strictly enforcing state transitions.
    """
    if ticket_update.status:
        if not validate_state_transition(ticket.status, ticket_update.status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state transition from '{ticket.status}' to '{ticket_update.status}'"
            )
        ticket.status = ticket_update.status
        if ticket.status == "resolved" and not ticket.resolved_at:
            ticket.resolved_at = datetime.now(timezone.utc)

    if ticket_update.priority:
        ticket.priority = ticket_update.priority
    if ticket_update.category:
        ticket.category = ticket_update.category
    if ticket_update.assigned_team_id:
        ticket.assigned_team_id = ticket_update.assigned_team_id
    if ticket_update.assigned_user_id:
        ticket.assigned_user_id = ticket_update.assigned_user_id

    db.commit()
    db.refresh(ticket)

    record_audit_event(
        db=db,
        organization_id=ticket.organization_id,
        action="ticket.updated",
        target_type="ticket",
        target_id=ticket.id,
        actor_id=actor_id,
        actor_email=actor_email,
        details={"updates": ticket_update.model_dump(exclude_unset=True)}
    )

    return ticket
