import pytest
from app.models.draft import ResponseDraft
from app.models.audit import AuditEvent


def test_ticket_creation_and_idempotency(client, seed_test_data):
    org_a = seed_test_data["org_a"]
    token_a = seed_test_data["token_a"]

    headers = {
        "Authorization": f"Bearer {token_a}",
        "X-Organization-ID": org_a.id
    }
    payload = {
        "subject": "Duplicate billing charge on card",
        "description": "I was charged twice for the monthly plan.",
        "source": "web",
        "idempotency_key": "idem-key-12345"
    }

    # 1. Create ticket
    res1 = client.post("/api/v1/tickets", json=payload, headers=headers)
    assert res1.status_code == 201
    ticket_id = res1.json()["id"]
    assert res1.json()["category"] == "billing"
    assert res1.json()["priority"] == "high"

    # 2. Idempotent re-submission with same idempotency key
    res2 = client.post("/api/v1/tickets", json=payload, headers=headers)
    assert res2.status_code == 201
    assert res2.json()["id"] == ticket_id


def test_human_approval_and_delivery_lifecycle(client, seed_test_data, db_session):
    org_a = seed_test_data["org_a"]
    token_a = seed_test_data["token_a"]

    headers = {
        "Authorization": f"Bearer {token_a}",
        "X-Organization-ID": org_a.id
    }

    # Create ticket
    payload = {
        "subject": "How to cancel my subscription?",
        "description": "Please provide the cancellation link.",
        "source": "api"
    }
    create_res = client.post("/api/v1/tickets", json=payload, headers=headers)
    assert create_res.status_code == 201
    ticket = create_res.json()
    ticket_id = ticket["id"]

    # Retrieve generated draft
    drafts_res = client.get(f"/api/v1/tickets/{ticket_id}/drafts", headers=headers)
    assert drafts_res.status_code == 200
    drafts = drafts_res.json()
    assert len(drafts) >= 1
    draft_id = drafts[0]["id"]
    assert drafts[0]["status"] == "draft"

    # Attempt to send UNAPPROVED draft -> MUST FAIL WITH 400
    unapproved_send = client.post(f"/api/v1/drafts/{draft_id}/send", headers=headers)
    assert unapproved_send.status_code == 400
    assert "Human approval is required" in unapproved_send.json()["detail"]

    # Approve draft
    approve_res = client.post(f"/api/v1/drafts/{draft_id}/approve", headers=headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    # Send approved draft -> MUST SUCCEED
    send_res = client.post(f"/api/v1/drafts/{draft_id}/send", headers=headers)
    assert send_res.status_code == 200
    assert send_res.json()["delivery_status"] == "delivered"

    # Verify ticket state is now 'sent'
    ticket_res = client.get(f"/api/v1/tickets/{ticket_id}", headers=headers)
    assert ticket_res.status_code == 200
    assert ticket_res.json()["status"] == "sent"
