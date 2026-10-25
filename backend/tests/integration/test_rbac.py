import pytest
from app.models.ticket import Ticket


def test_cross_tenant_access_is_forbidden(client, seed_test_data, db_session):
    org_a = seed_test_data["org_a"]
    org_b = seed_test_data["org_b"]
    token_b = seed_test_data["token_b"]

    # User B belongs to Org Beta, attempts to access Org Alpha's tickets
    headers = {
        "Authorization": f"Bearer {token_b}",
        "X-Organization-ID": org_a.id
    }
    response = client.get("/api/v1/tickets", headers=headers)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_authorized_tenant_access_succeeds(client, seed_test_data, db_session):
    org_a = seed_test_data["org_a"]
    token_a = seed_test_data["token_a"]

    headers = {
        "Authorization": f"Bearer {token_a}",
        "X-Organization-ID": org_a.id
    }
    response = client.get("/api/v1/tickets", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0
