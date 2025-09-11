import respx
import httpx
from app.domain.messaging.wa_client import WhatsAppClient
from app.core.config import settings


@respx.mock
def test_wa_client_send_text_success():
    client = WhatsAppClient(token="tkn", base_url="https://graph.facebook.com/v20.0", phone_number_id="123")
    route = respx.post("https://graph.facebook.com/v20.0/123/messages").mock(
        return_value=httpx.Response(200, json={"messages": [{"id": "wamid.abc"}]}),
    )
    resp = client.send_text(to_wa_id="5561999999999", text="Ola")
    assert route.called
    assert resp["messages"][0]["id"].startswith("wamid.")


@respx.mock
def test_wa_client_send_text_error_401():
    client = WhatsAppClient(token="bad", base_url="https://graph.facebook.com/v20.0", phone_number_id="123")
    respx.post("https://graph.facebook.com/v20.0/123/messages").mock(
        return_value=httpx.Response(401, json={"error": {"code": 190}}),
    )
    try:
        client.send_text(to_wa_id="5561999999999", text="Ola")
        assert False, "should raise"
    except httpx.HTTPStatusError as e:
        assert e.response.status_code == 401
