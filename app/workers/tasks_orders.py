from __future__ import annotations
from celery import Task
from app.workers.celery_app import celery
import structlog
from app.repositories.db import SessionLocal
from app.repositories import models
from app.workers.tasks_outbound import send_text as task_send_text

log = structlog.get_logger()


@celery.task(name="orders.set_status", bind=True, max_retries=3)
def set_status_task(self: Task, order_id: int, target_status: str):
    """Altera status de pedido de forma assíncrona e envia notificação.
    Usa a mesma matriz de transição da API e respeita allow_direct_paid quando relevante.
    """
    with SessionLocal() as db:
        order = db.get(models.Order, order_id)
        if not order:
            log.error("order_not_found", order_id=order_id)
            return {"ok": False, "error": "order_not_found"}

        tenant = db.get(models.Tenant, order.tenant_id)
        allow_direct_paid = bool((tenant.settings_json or {}).get("allow_direct_paid")) if tenant else False
        current = order.status
        target = models.OrderStatus(target_status)

        allowed: dict[models.OrderStatus, set[models.OrderStatus]] = {
            models.OrderStatus.draft: {models.OrderStatus.canceled},
            models.OrderStatus.pending_payment: {models.OrderStatus.paid, models.OrderStatus.canceled},
            models.OrderStatus.paid: {models.OrderStatus.in_kitchen, models.OrderStatus.canceled},
            models.OrderStatus.in_kitchen: {models.OrderStatus.out_for_delivery, models.OrderStatus.canceled},
            models.OrderStatus.out_for_delivery: {models.OrderStatus.delivered, models.OrderStatus.canceled},
            models.OrderStatus.delivered: set(),
            models.OrderStatus.canceled: set(),
        }
        if allow_direct_paid:
            allowed.setdefault(models.OrderStatus.draft, set()).add(models.OrderStatus.paid)
            allowed.setdefault(models.OrderStatus.in_kitchen, set()).add(models.OrderStatus.paid)
            allowed.setdefault(models.OrderStatus.out_for_delivery, set()).add(models.OrderStatus.paid)

        if target not in allowed.get(current, set()):
            log.warning("invalid_transition", current=current.value, target=target.value, order_id=order_id)
            return {"ok": False, "error": f"invalid_transition:{current.value}->{target.value}"}

        # Guardas mínimas para paid direto
        if target is models.OrderStatus.paid and allow_direct_paid:
            if not order.delivery_address:
                log.warning("address_required_for_paid", order_id=order_id)
                return {"ok": False, "error": "address_required"}

        order.status = target
        db.add(order)
        db.commit()
        db.refresh(order)

        # Notificação simples
        try:
            customer = db.get(models.Customer, order.customer_id)
            if customer and customer.wa_id:
                msg = {
                    models.OrderStatus.paid: "Pagamento confirmado! Seu pedido será preparado.",
                    models.OrderStatus.in_kitchen: "Seu pedido entrou em preparo.",
                    models.OrderStatus.out_for_delivery: "Seu pedido saiu para entrega.",
                    models.OrderStatus.delivered: "Pedido entregue. Bom apetite!",
                    models.OrderStatus.canceled: "Seu pedido foi cancelado.",
                }.get(order.status, f"Status do pedido atualizado: {order.status.value}")
                task_send_text.delay(
                    tenant_id=order.tenant_id,
                    to_wa_id=customer.wa_id,
                    text=msg,
                    idempotency_key=f"order-status-{order.id}-{order.status.value}",
                )
        except Exception:
            pass

    return {"ok": True, "order_id": order_id, "status": target.value}
