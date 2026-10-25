from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    id: str
    organization_id: str
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    action: str
    target_type: str
    target_id: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


class AuditEventListResponse(BaseModel):
    total: int
    items: List[AuditEventResponse]
