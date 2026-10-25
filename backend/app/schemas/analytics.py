from typing import Dict, List, Optional
from pydantic import BaseModel


class StatusCount(BaseModel):
    status: str
    count: int


class CategoryCount(BaseModel):
    category: str
    count: int


class PriorityCount(BaseModel):
    priority: str
    count: int


class AnalyticsOverview(BaseModel):
    ticket_volume: int
    first_response_time_seconds: float
    resolution_time_seconds: float
    escalation_rate: float
    draft_approval_rate: float
    ai_failure_rate: float
    average_processing_latency_ms: float
    by_status: List[StatusCount]
    by_category: List[CategoryCount]
    by_priority: List[PriorityCount]


class TicketTrendPoint(BaseModel):
    date: str
    created_count: int
    resolved_count: int


class AnalyticsTrends(BaseModel):
    trends: List[TicketTrendPoint]
