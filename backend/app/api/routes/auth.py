from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User, Membership
from app.models.organization import Organization
from app.schemas.auth import UserLogin, Token, UserResponse, MembershipResponse
from app.core.security import verify_password, create_access_token
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == login_in.email))
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch memberships
    memberships = db.scalars(
        select(Membership).where(Membership.user_id == user.id)
    ).all()
    
    membership_responses = []
    for m in memberships:
        org = db.get(Organization, m.organization_id)
        membership_responses.append(MembershipResponse(
            id=m.id,
            organization_id=m.organization_id,
            organization_name=org.name if org else None,
            role=m.role,
            created_at=m.created_at
        ))

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email}
    )

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        memberships=membership_responses
    )

    return Token(access_token=access_token, token_type="bearer", user=user_resp)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.scalars(
        select(Membership).where(Membership.user_id == current_user.id)
    ).all()
    
    membership_responses = []
    for m in memberships:
        org = db.get(Organization, m.organization_id)
        membership_responses.append(MembershipResponse(
            id=m.id,
            organization_id=m.organization_id,
            organization_name=org.name if org else None,
            role=m.role,
            created_at=m.created_at
        ))

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
        memberships=membership_responses
    )
