from __future__ import annotations
from typing import Optional, Dict, Any, List
import structlog

log = structlog.get_logger()


class NoopProvider:
    """Provider que não envia nada (para DEV). Apenas loga as operações."""

    def send_text(self, to: str, text: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        log.info("noop_send_text", to=to, text=text[:200])
        return {"provider": "noop", "to": to, "ok": True}

    def send_template(
        self,
        to: str,
        template_name: str,
        language: str = "pt_BR",
        components: Optional[List[Dict[str, Any]]] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        log.info("noop_send_template", to=to, template=template_name, language=language, components=components)
        return {"provider": "noop", "to": to, "ok": True}

    def mark_read(self, message_id: str) -> Dict[str, Any]:
        log.info("noop_mark_read", message_id=message_id)
        return {"provider": "noop", "message_id": message_id, "ok": True}
