from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_leads_staging_create_then_update():
    # Create
    body1 = {
        "external_lead_id": "X-42",
        "source": "portalA",
        "name": "Fulano",
        "phone": "+5511999990000",
        "email": "fulano@exemplo.com",
        "preferences": {"finalidade": "sale", "cidade": "São Paulo"},
        "updated_at_source": "2025-09-15T12:00:00Z",
    }
    r1 = client.post("/re/leads/staging", json=body1)
    assert r1.status_code == 200, r1.text
    data1 = r1.json()
    assert data1["lead"]["telefone"] == "+5511999990000"
    assert data1["lead"]["preferencias"]["external_lead_id"] == "X-42"
    assert data1["lead"]["preferencias"]["updated_at_source"] == "2025-09-15T12:00:00Z"

    # Update (merge preferences and update updated_at_source)
    body2 = {
        "external_lead_id": "X-42",
        "source": "portalA",
        "name": "Fulano de Tal",
        "phone": "+5511999990000",
        "preferences": {"tipo": "apartment"},
        "updated_at_source": "2025-09-15T12:05:00Z",
    }
    r2 = client.post("/re/leads/staging", json=body2)
    assert r2.status_code == 200, r2.text
    data2 = r2.json()
    assert data2["updated"] is True
    prefs = data2["lead"]["preferencias"]
    # Check merge
    assert prefs["finalidade"] == "sale"
    assert prefs["cidade"] == "São Paulo"
    assert prefs["tipo"] == "apartment"
    assert prefs["external_lead_id"] == "X-42"
    assert prefs["updated_at_source"] == "2025-09-15T12:05:00Z"
