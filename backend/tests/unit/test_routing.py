import pytest
from app.services.routing_service import evaluate_escalation, resolve_team_for_ticket
from app.models.team import Team


def test_security_mandatory_escalation():
    priority, needs_triage, reason = evaluate_escalation(
        category="security",
        priority="normal",
        sentiment="neutral",
        content="We detected a security breach and unauthorized database exploit."
    )
    assert priority == "urgent"
    assert needs_triage is True
    assert "Security" in reason


def test_frustration_priority_escalation():
    priority, needs_triage, reason = evaluate_escalation(
        category="billing",
        priority="normal",
        sentiment="frustrated",
        content="I am furious about this billing charge!"
    )
    assert priority == "high"
    assert "frustration" in reason.lower()


def test_normal_priority_preserved():
    priority, needs_triage, reason = evaluate_escalation(
        category="general",
        priority="normal",
        sentiment="neutral",
        content="What are your holiday hours?"
    )
    assert priority == "normal"
    assert needs_triage is False
    assert reason is None
