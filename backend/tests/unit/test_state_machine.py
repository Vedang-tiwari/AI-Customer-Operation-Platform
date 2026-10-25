import pytest
from app.services.ticket_service import validate_state_transition


def test_valid_ticket_lifecycle_transitions():
    assert validate_state_transition("received", "processing") is True
    assert validate_state_transition("processing", "awaiting_review") is True
    assert validate_state_transition("awaiting_review", "approved") is True
    assert validate_state_transition("approved", "sending") is True
    assert validate_state_transition("sending", "sent") is True
    assert validate_state_transition("sent", "resolved") is True
    # Reopening allowed
    assert validate_state_transition("resolved", "received") is True


def test_invalid_ticket_lifecycle_transitions():
    # Direct skip to sent without approval is strictly forbidden
    assert validate_state_transition("received", "sent") is False
    assert validate_state_transition("awaiting_review", "sent") is False
    assert validate_state_transition("sending", "received") is False
    assert validate_state_transition("sent", "processing") is False
