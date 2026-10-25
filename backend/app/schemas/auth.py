from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: Optional[str] = "Default Organization"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    org_id: Optional[str] = None
    role: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MembershipResponse(BaseModel):
    id: str
    organization_id: str
    organization_name: Optional[str] = None
    role: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    memberships: List[MembershipResponse] = []
    model_config = ConfigDict(from_attributes=True)


class MemberAdd(BaseModel):
    email: EmailStr
    role: str = "agent"  # admin, manager, agent
