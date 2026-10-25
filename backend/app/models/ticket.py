from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, generate_uuid


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_org_status", "organization_id", "status"),
        Index("ix_tickets_org_idempotency", "organization_id", "idempotency_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="api", nullable=False)  # api, web, webhook, email
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # State & AI Classification
    status: Mapped[str] = mapped_column(String(50), default="received", index=True, nullable=False)
    # Allowed statuses: received, processing, needs_triage, awaiting_review, approved, sending, sent, resolved
    priority: Mapped[str] = mapped_column(String(50), default="normal", index=True, nullable=False)
    # Allowed priorities: urgent, high, normal, low
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    # billing, technical, security, account, general
    sentiment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # positive, neutral, negative, frustrated
    intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=True)

    # Ownership & Routing
    assigned_team_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    assigned_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="tickets")
    assigned_team = relationship("Team", back_populates="tickets")
    assigned_user = relationship("User")
    messages = relationship("Message", back_populates="ticket", cascade="all, delete-orphan", order_by="Message.created_at")
    drafts = relationship("ResponseDraft", back_populates="ticket", cascade="all, delete-orphan", order_by="ResponseDraft.created_at.desc()")
    jobs = relationship("ProcessingJob", back_populates="ticket", cascade="all, delete-orphan")
