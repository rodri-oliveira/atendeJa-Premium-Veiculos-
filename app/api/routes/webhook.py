from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from app.core.config import settings
import structlog
from app.workers.tasks_inbound import buffer_incoming_message
import hmac
import hashlib
from app.repositories.db import SessionLocal
from sqlalchemy.orm import Session
from app.repositories import models
from app.api.routes.orders import _recalc_totals  # reuse helper
from pydantic import BaseModel
from typing import Literal
from app.workers.tasks_orders import set_status_task

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
    # Optional: validate HMAC from Meta if secret configured
    try:
        secret = settings.WA_WEBHOOK_SECRET
    except Exception:
        secret = ""
    signature = request.headers.get("x-hub-signature-256")
    if secret:
        if not signature or not signature.startswith("sha256="):
            log.error("webhook_hmac_missing_or_malformed")
            return {"received": True, "error": "invalid_signature"}
        expected = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        provided = signature.split("=", 1)[1]
        if not hmac.compare_digest(expected, provided):
            log.error("webhook_hmac_mismatch")
            return {"received": True, "error": "invalid_signature"}
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


class PaymentEvent(BaseModel):
    order_id: int
    payment_id: str | None = None
    status: Literal["paid"]


@router.post("/payments")
async def payments_webhook(body: PaymentEvent):
    """Webhook mock de pagamentos. Envie um JSON com o formato:
    {"order_id": 1, "payment_id": "uuid", "status": "paid"}
    Marca o pedido como 'paid' respeitando regras do tenant.
    """
    order_id = body.order_id
    payment_status = body.status

    with SessionLocal() as db:  # type: Session
        order = db.get(models.Order, int(order_id))
        if not order:
            raise HTTPException(status_code=404, detail="order_not_found")

        tenant = db.get(models.Tenant, order.tenant_id)
        allow_direct_paid = bool((tenant.settings_json or {}).get("allow_direct_paid")) if tenant else False

        current = order.status
        # Permite pending_payment sempre; permite saltos se flag ativada (com endereço)
        can_mark = current == models.OrderStatus.pending_payment or (
            allow_direct_paid and current in {models.OrderStatus.draft, models.OrderStatus.in_kitchen, models.OrderStatus.out_for_delivery}
        )
        if not can_mark:
            raise HTTPException(status_code=400, detail=f"invalid_transition:{current.value}->paid")

        if not order.delivery_address:
            raise HTTPException(status_code=400, detail="address_required")

        db.flush()
        _recalc_totals(db, order)
        order.status = models.OrderStatus.paid
        db.add(order)
        try:
            db.add(models.OrderStatusEvent(order_id=order.id, from_status=current.value, to_status=models.OrderStatus.paid.value))
        except Exception:
            pass
        db.commit()
        db.refresh(order)

        # Notificar cliente
        try:
            customer = db.get(models.Customer, order.customer_id)
            if customer and customer.wa_id:
                from app.workers.tasks_outbound import send_text as task_send_text

                task_send_text.delay(
                    tenant_id=order.tenant_id,
                    wa_id=customer.wa_id,
                    text="Pagamento confirmado! Seu pedido será preparado.",
                    idempotency_key=f"order-status-{order.id}-paid",
                )
        except Exception:
            pass

        # Agenda próxima etapa automática: paid -> in_kitchen (somente se auto_progress_enabled=true)
        try:
            cfg = (tenant.settings_json or {}) if tenant else {}
            if cfg.get("auto_progress_enabled"):
                sla_preparo_min = int(cfg.get("sla_preparo_min", 10))
                countdown = max(0, sla_preparo_min) * 60
                set_status_task.apply_async(
                    kwargs={"order_id": order.id, "target_status": "in_kitchen"}, countdown=countdown
                )
        except Exception:
            pass

    return {"received": True, "order_id": order.id, "status": order.status.value}
