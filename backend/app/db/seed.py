from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User, Membership
from app.models.team import Team
from app.models.ticket import Ticket
from app.models.message import Message
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.models.draft import ResponseDraft, Citation
from app.models.audit import AuditEvent
from app.models.job import ProcessingJob
from app.ai.embeddings import generate_embedding
from app.services.knowledge_service import chunk_text
from app.core.logging import logger


def seed_database():
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_org = db.scalar(select(Organization))
        if existing_org:
            logger.info("Database is already seeded. Skipping initial seeding.")
            return

        logger.info("Seeding organizations...")
        org1 = Organization(
            name="Acme Cloud SaaS",
            slug="acme-cloud",
            settings={"tier": "enterprise", "timezone": "America/New_York"}
        )
        org2 = Organization(
            name="FinFlow Payments",
            slug="finflow-pay",
            settings={"tier": "growth", "timezone": "Europe/London"}
        )
        db.add_all([org1, org2])
        db.commit()

        logger.info("Seeding users...")
        pwd_hash = hash_password("password123")
        
        user_admin = User(
            email="admin@acme.com",
            full_name="Sarah Connor (Acme Admin)",
            hashed_password=pwd_hash,
            is_active=True,
            is_superuser=True
        )
        user_agent = User(
            email="agent@acme.com",
            full_name="Alex Smith (Support Agent)",
            hashed_password=pwd_hash,
            is_active=True
        )
        user_manager = User(
            email="manager@finflow.com",
            full_name="Elena Rostova (FinFlow Ops)",
            hashed_password=pwd_hash,
            is_active=True
        )
        db.add_all([user_admin, user_agent, user_manager])
        db.commit()

        logger.info("Seeding memberships...")
        m1 = Membership(organization_id=org1.id, user_id=user_admin.id, role="admin")
        m2 = Membership(organization_id=org1.id, user_id=user_agent.id, role="agent")
        m3 = Membership(organization_id=org2.id, user_id=user_manager.id, role="manager")
        # Give admin access to both orgs for smooth demoing
        m4 = Membership(organization_id=org2.id, user_id=user_admin.id, role="admin")
        db.add_all([m1, m2, m3, m4])
        db.commit()

        logger.info("Seeding teams...")
        team_billing = Team(organization_id=org1.id, name="Billing Support", description="Subscription disputes and invoices")
        team_tech = Team(organization_id=org1.id, name="Technical Support", description="API, latency, and platform bugs")
        team_sec = Team(organization_id=org1.id, name="Security & Compliance", description="Data privacy, SOC2, incidents")
        team_gen = Team(organization_id=org1.id, name="General Support", description="Tier 1 customer inquiries")

        team_fin_ops = Team(organization_id=org2.id, name="Merchant Operations", description="Payouts and onboarding")
        team_fin_fraud = Team(organization_id=org2.id, name="Fraud & Risk", description="Chargebacks and AML checks")
        db.add_all([team_billing, team_tech, team_sec, team_gen, team_fin_ops, team_fin_fraud])
        db.commit()

        logger.info("Seeding knowledge documents...")
        refund_text = """Our standard refund policy permits customers to request a full refund within 30 days of the subscription purchase date. Refund requests submitted after 30 days are non-refundable.

If a customer is inadvertently billed twice due to network retries, our operations team will immediately verify transaction logs and issue an automated refund for the duplicate charge within 1 to 2 business days."""

        rate_limit_text = """All API requests are authenticated via Bearer tokens. Standard tier accounts have a limit of 1,000 requests per minute per organization token. Exceeding this rate returns HTTP 429 Too Many Requests with a Retry-After header.

Webhook integrations should use the event_id header to deduplicate messages. Repeated webhook deliveries within 24 hours are safely acknowledged without re-execution."""

        sla_text = """Severity 1 (Urgent): System down or security breach. Target response time is under 15 minutes with 24/7 on-call engineering.
Severity 2 (High): Critical functionality impaired. Target response time is under 1 hour.
Severity 3 (Normal): General inquiries. Response time target is within 4 business hours."""

        doc1 = KnowledgeDocument(
            organization_id=org1.id,
            title="Acme Refund & Billing Policy",
            file_type="text/markdown",
            status="indexed"
        )
        doc2 = KnowledgeDocument(
            organization_id=org1.id,
            title="Acme REST API Rate Limits & Webhooks",
            file_type="text/markdown",
            status="indexed"
        )
        doc3 = KnowledgeDocument(
            organization_id=org2.id,
            title="FinFlow SLA & Escalation Guidelines",
            file_type="text/markdown",
            status="indexed"
        )
        db.add_all([doc1, doc2, doc3])
        db.commit()

        # Add chunks for doc1
        for i, passage in enumerate(chunk_text(refund_text)):
            c = DocumentChunk(
                document_id=doc1.id,
                chunk_index=i,
                content=passage,
                embedding=generate_embedding(passage),
                token_count=len(passage.split())
            )
            db.add(c)

        # Add chunks for doc2
        for i, passage in enumerate(chunk_text(rate_limit_text)):
            c = DocumentChunk(
                document_id=doc2.id,
                chunk_index=i,
                content=passage,
                embedding=generate_embedding(passage),
                token_count=len(passage.split())
            )
            db.add(c)

        # Add chunks for doc3
        for i, passage in enumerate(chunk_text(sla_text)):
            c = DocumentChunk(
                document_id=doc3.id,
                chunk_index=i,
                content=passage,
                embedding=generate_embedding(passage),
                token_count=len(passage.split())
            )
            db.add(c)
        db.commit()

        logger.info("Seeding sample tickets...")
        # Ticket 1 (Acme - Billing)
        t1 = Ticket(
            organization_id=org1.id,
            subject="Duplicate subscription charge on Visa",
            description="I was billed twice for my pro subscription on October 24th ($49 x 2). Please refund the duplicate transaction immediately.",
            source="web",
            status="awaiting_review",
            priority="high",
            category="billing",
            sentiment="frustrated",
            intent="duplicate_charge",
            confidence_score=0.96,
            assigned_team_id=team_billing.id
        )
        db.add(t1)
        db.commit()

        # Initial message
        m_t1 = Message(ticket_id=t1.id, sender_type="customer", sender_name="Jane Doe", body=t1.description)
        db.add(m_t1)
        db.commit()

        # Response draft with citation
        c1 = db.scalar(select(DocumentChunk).where(DocumentChunk.document_id == doc1.id))
        draft1 = ResponseDraft(
            ticket_id=t1.id,
            body=(
                "Hello Jane,\n\n"
                "Thank you for contacting Acme Support regarding the duplicate subscription charge. "
                "I apologize for the inconvenience.\n\n"
                "According to our official policy, our operations team verifies duplicate charges and issues an automated refund within 1 to 2 business days [Source: " + (c1.id if c1 else "chunk-1") + "]. "
                "I have initiated the refund for the extra $49 charge back to your original Visa card.\n\n"
                "Best regards,\nAcme Support Team"
            ),
            status="draft",
            created_by_model="grounded-rag-engine-v1",
            confidence_score=0.94
        )
        db.add(draft1)
        db.commit()

        if c1:
            cit1 = Citation(
                draft_id=draft1.id,
                chunk_id=c1.id,
                passage_snippet=c1.content[:150],
                relevance_score=0.92
            )
            db.add(cit1)

        # Ticket 2 (Acme - Technical)
        t2 = Ticket(
            organization_id=org1.id,
            subject="API Rate Limit 429 when receiving webhook payloads",
            description="Our service is hitting HTTP 429 Too Many Requests on the webhook endpoint during peak batch sync.",
            source="api",
            status="needs_triage",
            priority="normal",
            category="technical",
            sentiment="neutral",
            intent="api_error",
            confidence_score=0.89,
            assigned_team_id=team_tech.id
        )
        db.add(t2)
        db.commit()

        # Ticket 3 (Acme - Security Urgent)
        t3 = Ticket(
            organization_id=org1.id,
            subject="Security: Unknown IP generating API keys in dashboard",
            description="We observed unauthorized access and new API tokens created from an unrecognized IP address. Immediate assistance required!",
            source="web",
            status="needs_triage",
            priority="urgent",
            category="security",
            sentiment="negative",
            intent="security_incident",
            confidence_score=0.98,
            assigned_team_id=team_sec.id
        )
        db.add(t3)
        db.commit()

        # Ticket 4 (FinFlow - Compliance)
        t4 = Ticket(
            organization_id=org2.id,
            subject="Merchant KYC verification document upload",
            description="Where should our legal team upload the updated certificate of incorporation for our merchant account?",
            source="web",
            status="awaiting_review",
            priority="normal",
            category="account",
            sentiment="neutral",
            intent="account_management",
            confidence_score=0.88,
            assigned_team_id=team_fin_ops.id
        )
        db.add(t4)
        db.commit()

        # Seed audit events
        record_1 = AuditEvent(
            organization_id=org1.id,
            actor_id=user_admin.id,
            actor_email=user_admin.email,
            action="system.seeded",
            target_type="organization",
            target_id=org1.id,
            details={"demo_seeded": True}
        )
        db.add(record_1)
        db.commit()

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
