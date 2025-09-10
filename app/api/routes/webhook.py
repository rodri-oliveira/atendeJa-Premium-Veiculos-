from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from app.core.config import settings
import structlog
from app.workers.tasks_inbound import buffer_incoming_message

router = APIRouter()
log = structlog.get_logger()


@router.get("")
async def verify(
    request: Request,
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
):
    """
    Meta sends the verification GET with query params using the 'hub.' prefix.
    Example: /webhook?hub.mode=subscribe&hub.challenge=123&hub.verify_token=xxx
    """
    if hub_verify_token != settings.WA_VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid verify token")
    # Return the challenge as plain text
    return PlainTextResponse(hub_challenge or "")


@router.post("")
async def receive(request: Request):
    # Read raw body to handle different encodings safely
    import json  # local import to avoid global overhead
    body_bytes: bytes = await request.body()
    payload = None
    if not body_bytes:
        log.error("webhook_json_error", error="empty body")
        return {"received": True, "error": "invalid_json"}
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            payload = json.loads(body_bytes.decode(enc))
            break
        except Exception:  # noqa: BLE001
            payload = None
            continue
    if payload is None:
        try:
            # As a last resort, try FastAPI's parser
            payload = await request.json()
        except Exception as e:  # noqa: BLE001
            log.error("webhook_json_error", error=str(e))
            return {"received": True, "error": "invalid_json"}

    log.info("webhook_received", payload=payload)
    # Basic WhatsApp payload extraction (text messages)
    try:
        entries = payload.get("entry", []) or []
        for entry in entries:
            changes = entry.get("changes", []) or []
            for change in changes:
                value = change.get("value", {}) or {}
                messages = value.get("messages", []) or []
                contacts = value.get("contacts", []) or []
                wa_id = None
                if contacts:
                    wa_id = contacts[0].get("wa_id")
                for msg in messages:
                    if not wa_id:
                        wa_id = msg.get("from")
                    msg_type = msg.get("type")
                    if msg_type == "text":
                        text = (msg.get("text", {}) or {}).get("body", "").strip()
                        if text:
                            buffer_incoming_message.delay(
                                settings.DEFAULT_TENANT_ID,
                                wa_id or "unknown",
                                text,
                                payload,
                            )
        return {"received": True}
    except Exception as e:  # noqa: BLE001
        log.error("webhook_process_error", error=str(e))
        # Always 200 to avoid Meta retries storm; errors are handled internally
        return {"received": True, "error": "processing"}
