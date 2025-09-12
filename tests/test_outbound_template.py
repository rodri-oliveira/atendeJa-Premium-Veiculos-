import respx
import httpx
from app.domain.messaging.wa_client import WhatsAppClient


@respx.mock
def test_wa_client_send_template_success():
    client = WhatsAppClient(token="tkn", base_url="https://graph.facebook.com/v20.0", phone_number_id="123")
    route = respx.post("https://graph.facebook.com/v20.0/123/messages").mock(
        return_value=httpx.Response(200, json={"messages": [{"id": "wamid.template"}]}),
    )
    resp = client.send_template(
        to_wa_id="5561999999999",
        template_name="hello_world",
        language_code="pt_BR",
        components=[{"type": "body", "parameters": [{"type": "text", "text": "Rodrigo"}]}],
    )
    assert route.called
    assert resp["messages"][0]["id"].startswith("wamid.")


@respx.mock
def test_wa_client_send_template_error_400():
    client = WhatsAppClient(token="bad", base_url="https://graph.facebook.com/v20.0", phone_number_id="123")
    respx.post("https://graph.facebook.com/v20.0/123/messages").mock(
        return_value=httpx.Response(400, json={"error": {"message": "template not approved"}}),
    )
    try:
        client.send_template(to_wa_id="5561999999999", template_name="hello_world")
        assert False, "should raise"
    except httpx.HTTPStatusError as e:
        assert e.response.status_code == 400
