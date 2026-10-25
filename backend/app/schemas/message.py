from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    body: str
    sender_type: str = "agent"  # agent, customer, internal
    sender_name: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    ticket_id: str
    sender_type: str
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    body: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
