from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.message import MessageResponse
from app.schemas.draft import DraftResponse


class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    source: str = "api"  # api, web, webhook, email
    external_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_team_id: Optional[str] = None
    assigned_user_id: Optional[str] = None


class TicketEscalateRequest(BaseModel):
    reason: str
    target_priority: str = "urgent"


class TeamBrief(BaseModel):
    id: str
    name: str
    model_config = ConfigDict(from_attributes=True)


class TicketResponse(BaseModel):
    id: str
    organization_id: str
    subject: str
    description: str
    source: str
    external_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    status: str
    priority: str
    category: Optional[str] = None
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    confidence_score: Optional[float] = None
    needs_human_review: bool
    assigned_team_id: Optional[str] = None
    assigned_team: Optional[TeamBrief] = None
    assigned_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    messages: List[MessageResponse] = []
    drafts: List[DraftResponse] = []
    model_config = ConfigDict(from_attributes=True)


class TicketListResponse(BaseModel):
    total: int
    items: List[TicketResponse]
