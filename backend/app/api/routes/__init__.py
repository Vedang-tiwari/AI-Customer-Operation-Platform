from fastapi import APIRouter
from app.api.routes import (
    auth,
    organizations,
    tickets,
    knowledge,
    drafts,
    analytics,
    audit,
    webhooks,
    health
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(tickets.router)
api_router.include_router(knowledge.router)
api_router.include_router(drafts.router)
api_router.include_router(analytics.router)
api_router.include_router(audit.router)
api_router.include_router(webhooks.router)
