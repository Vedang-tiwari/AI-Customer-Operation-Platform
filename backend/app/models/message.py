from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, generate_uuid


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    
    sender_type: Mapped[str] = mapped_column(String(50), nullable=False)  # customer, agent, system, internal
    sender_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # User ID if agent, or customer identifier
    sender_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    ticket = relationship("Ticket", back_populates="messages")
