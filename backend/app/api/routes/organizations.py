from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User, Membership
from app.schemas.auth import OrganizationResponse, MembershipResponse, MemberAdd
from app.api.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=List[OrganizationResponse])
def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List organizations the caller belongs to."""
    if current_user.is_superuser:
        orgs = db.scalars(select(Organization)).all()
    else:
        orgs = db.scalars(
            select(Organization)
            .join(Membership, Organization.id == Membership.organization_id)
            .where(Membership.user_id == current_user.id)
        ).all()
    return orgs


@router.get("/{org_id}/members", response_model=List[MembershipResponse])
def list_organization_members(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List members belonging to an organization."""
    # Verify membership
    if not current_user.is_superuser:
        user_mem = db.scalar(
            select(Membership).where(
                Membership.user_id == current_user.id,
                Membership.organization_id == org_id
            )
        )
        if not user_mem:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    memberships = db.scalars(
        select(Membership).where(Membership.organization_id == org_id)
    ).all()
    
    org = db.get(Organization, org_id)
    results = []
    for m in memberships:
        results.append(MembershipResponse(
            id=m.id,
            organization_id=m.organization_id,
            organization_name=org.name if org else None,
            role=m.role,
            created_at=m.created_at
        ))
    return results


@router.post("/{org_id}/members", response_model=MembershipResponse)
def add_organization_member(
    org_id: str,
    member_in: MemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a member to an organization (Admin only)."""
    # Verify admin role
    if not current_user.is_superuser:
        user_mem = db.scalar(
            select(Membership).where(
                Membership.user_id == current_user.id,
                Membership.organization_id == org_id,
                Membership.role == "admin"
            )
        )
        if not user_mem:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    target_user = db.scalar(select(User).where(User.email == member_in.email))
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = db.scalar(
        select(Membership).where(
            Membership.user_id == target_user.id,
            Membership.organization_id == org_id
        )
    )
    if existing:
        existing.role = member_in.role
        db.commit()
        db.refresh(existing)
        return existing

    new_mem = Membership(
        organization_id=org_id,
        user_id=target_user.id,
        role=member_in.role
    )
    db.add(new_mem)
    db.commit()
    db.refresh(new_mem)
    return new_mem
