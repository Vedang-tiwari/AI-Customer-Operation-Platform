from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CitationResponse(BaseModel):
    id: str
    chunk_id: str
    passage_snippet: Optional[str] = None
    relevance_score: Optional[float] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DraftResponse(BaseModel):
    id: str
    ticket_id: str
    body: str
    status: str  # draft, approved, rejected
    created_by_model: str
    confidence_score: Optional[float] = None
    rejection_reason: Optional[str] = None
    reviewed_by_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    citations: List[CitationResponse] = []
    model_config = ConfigDict(from_attributes=True)


class DraftUpdate(BaseModel):
    body: str


class DraftReject(BaseModel):
    reason: str


class DraftSendResponse(BaseModel):
    success: bool
    ticket_id: str
    draft_id: str
    delivery_status: str
    message: str
