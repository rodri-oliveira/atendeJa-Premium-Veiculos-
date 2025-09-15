from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ops_config_contract():
    r = client.get("/ops/config")
    assert r.status_code == 200, r.text
    data = r.json()
    # keys expected
    for k in ["app_env", "wa_provider", "default_tenant", "re_read_only", "version"]:
        assert k in data
    # types
    assert isinstance(data["app_env"], str)
    assert isinstance(data["wa_provider"], str)
    assert isinstance(data["default_tenant"], str)
    assert isinstance(data["re_read_only"], bool)
    assert isinstance(data["version"], str)
