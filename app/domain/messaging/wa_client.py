from __future__ import annotations
import httpx
import structlog
from app.core.config import settings

log = structlog.get_logger()


class WhatsAppClient:
    def __init__(self, token: str | None = None, base_url: str | None = None, phone_number_id: str | None = None):
        self.token = token or settings.WA_TOKEN
        self.base_url = (base_url or settings.WA_API_BASE).rstrip("/")
        self.phone_number_id = phone_number_id or settings.WA_PHONE_NUMBER_ID

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def send_text(self, to_wa_id: str, text: str) -> dict:
        """Send a simple text message via WhatsApp Cloud API.
        Returns JSON response or raises httpx.HTTPStatusError
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_wa_id,
            "type": "text",
            "text": {"body": text},
        }
        log.info("wa_send_text_request", to=to_wa_id)
        with httpx.Client(timeout=20) as client:
            resp = client.post(url, headers=self._headers(), json=payload)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                log.error("wa_send_text_error", status_code=resp.status_code, body=resp.text)
                raise e
            data = resp.json()
            log.info("wa_send_text_response", to=to_wa_id, response=data)
            return data

    def send_template(self, to_wa_id: str, template_name: str, language_code: str = "pt_BR", components: list[dict] | None = None) -> dict:
        """Send a template message to initiate a conversation outside 24h window.
        components follows Cloud API spec, e.g. [{"type":"body","parameters":[{"type":"text","text":"Rodrigo"}]}]
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_wa_id,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
        if components:
            payload["template"]["components"] = components
        log.info("wa_send_template_request", to=to_wa_id, template=template_name)
        with httpx.Client(timeout=20) as client:
            resp = client.post(url, headers=self._headers(), json=payload)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                log.error("wa_send_template_error", status_code=resp.status_code, body=resp.text)
                raise e
            data = resp.json()
            log.info("wa_send_template_response", to=to_wa_id, response=data)
            return data


def get_wa_client() -> WhatsAppClient:
    return WhatsAppClient()
