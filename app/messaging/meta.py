from __future__ import annotations
import httpx
from typing import Optional, Dict, Any, List
import time


class MetaCloudProvider:
    def __init__(self, api_base: str, token: str, phone_number_id: str) -> None:
        self.api_base = api_base.rstrip("/")
        self.token = token
        self.phone_number_id = phone_number_id
        self._client = httpx.Client(timeout=15.0)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _messages_url(self) -> str:
        return f"{self.api_base}/{self.phone_number_id}/messages"

    def _post_with_retry(self, url: str, json: Dict[str, Any], max_attempts: int = 3) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                r = self._client.post(url, headers=self._headers(), json=json)
                r.raise_for_status()
                return r
            except Exception as exc:
                last_exc = exc
                # Backoff exponencial curto: 0.3s, 0.6s
                if attempt < max_attempts:
                    time.sleep(0.3 * (2 ** (attempt - 1)))
        # Se esgotou tentativas, relança a última exceção
        assert last_exc is not None
        raise last_exc

    def send_text(self, to: str, text: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text[:4096]},
        }
        r = self._post_with_retry(self._messages_url(), payload)
        return r.json()

    def send_template(
        self,
        to: str,
        template_name: str,
        language: str = "pt_BR",
        components: Optional[List[Dict[str, Any]]] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }
        if components:
            payload["template"]["components"] = components
        r = self._post_with_retry(self._messages_url(), payload)
        return r.json()

    def mark_read(self, message_id: str) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        r = self._post_with_retry(self._messages_url(), payload)
        return r.json()
