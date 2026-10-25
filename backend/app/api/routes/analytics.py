from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.organization import Organization
from app.schemas.analytics import AnalyticsOverview, AnalyticsTrends
from app.services.analytics_service import get_operational_overview, get_ticket_trends
from app.api.dependencies import get_current_organization

router = APIRouter(prefix="/analytics", tags=["Operational Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Retrieve operational KPIs, response times, approval rates, and distributions."""
    return get_operational_overview(db=db, organization_id=org.id)


@router.get("/tickets", response_model=AnalyticsTrends)
def get_analytics_trends(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Retrieve 7-day ticket trends for volume and resolutions."""
    return get_ticket_trends(db=db, organization_id=org.id)
