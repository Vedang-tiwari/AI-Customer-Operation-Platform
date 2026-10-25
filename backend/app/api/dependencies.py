from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User, Membership
from app.models.organization import Organization


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts, validates JWT access token and loads current active user.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload["sub"]
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_organization(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Organization:
    """
    Derives organization tenant context and strictly verifies user membership.
    Prevents cross-tenant unauthorized data access.
    """
    target_org_id = x_organization_id

    # If no specific org header provided, fallback to user's first membership
    if not target_org_id:
        membership = db.scalar(
            select(Membership).where(Membership.user_id == current_user.id)
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to any organization"
            )
        target_org_id = membership.organization_id

    # Verify user's membership in the target organization
    if not current_user.is_superuser:
        user_membership = db.scalar(
            select(Membership).where(
                Membership.user_id == current_user.id,
                Membership.organization_id == target_org_id
            )
        )
        if not user_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: User is not an authorized member of this organization"
            )

    org = db.get(Organization, target_org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return org


def require_roles(allowed_roles: List[str]):
    """
    Role-Based Access Control (RBAC) dependency validator.
    """
    def role_checker(
        current_user: User = Depends(get_current_user),
        org: Organization = Depends(get_current_organization),
        db: Session = Depends(get_db)
    ) -> Membership:
        if current_user.is_superuser:
            # Synthetic membership for superuser
            return Membership(user_id=current_user.id, organization_id=org.id, role="admin")

        membership = db.scalar(
            select(Membership).where(
                Membership.user_id == current_user.id,
                Membership.organization_id == org.id
            )
        )
        if not membership or membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires one of the following roles: {allowed_roles}"
            )
        return membership

    return role_checker
