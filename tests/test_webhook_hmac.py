import hmac
import hashlib
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_webhook_post_hmac_ok():
    client = TestClient(app)
    secret_old = settings.WA_WEBHOOK_SECRET
    settings.WA_WEBHOOK_SECRET = "secret"
    try:
        body = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "contacts": [{"wa_id": "5561999999999"}],
                                "messages": [
                                    {
                                        "from": "5561999999999",
                                        "type": "text",
                                        "text": {"body": "Ola"},
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        }
        import json

        raw = json.dumps(body).encode("utf-8")
        sig = _sign(settings.WA_WEBHOOK_SECRET, raw)
        resp = client.post("/webhook", content=raw, headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"})
        assert resp.status_code == 200
        assert resp.json().get("received") is True
    finally:
        settings.WA_WEBHOOK_SECRET = secret_old


def test_webhook_post_hmac_invalid():
    client = TestClient(app)
    secret_old = settings.WA_WEBHOOK_SECRET
    settings.WA_WEBHOOK_SECRET = "secret"
    try:
        import json

        raw = json.dumps({"entry": []}).encode("utf-8")
        # wrong signature
        resp = client.post("/webhook", content=raw, headers={"X-Hub-Signature-256": "sha256=deadbeef", "Content-Type": "application/json"})
        assert resp.status_code == 200
        assert resp.json().get("error") == "invalid_signature"
    finally:
        settings.WA_WEBHOOK_SECRET = secret_old
