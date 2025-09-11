from __future__ import annotations
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError, Field
from sqlalchemy.orm import Session
from app.repositories.db import SessionLocal
from app.repositories import models
from app.core.config import settings
from app.domain.pizza.rules import is_open_now, delivery_fee_for
from app.workers.tasks_outbound import send_text as task_send_text
from app.workers.tasks_orders import set_status_task

router = APIRouter()


class OrderItemIn(BaseModel):
    menu_item_id: int
    qty: int = Field(default=1, ge=1)
    options: dict | None = None


class OrderCreate(BaseModel):
    wa_id: str
    first_item: OrderItemIn
    notes: Optional[str] = None


class OrderAddItem(BaseModel):
    menu_item_id: int
    qty: int = Field(default=1, ge=1)
    options: dict | None = None


class Address(BaseModel):
    street: str
    number: str
    district: str
    city: str
    state: str
    cep: str = Field(pattern=r"^\d{5}-?\d{3}$")


class OrderSetAddress(BaseModel):
    address: Address


class OrderConfirm(BaseModel):
    confirm: bool = True


class OrderSetStatus(BaseModel):
    status: Literal[
        "in_kitchen",
        "out_for_delivery",
        "delivered",
        "canceled",
        "paid",
    ]


def _recalc_totals(db: Session, order: models.Order) -> None:
    total_items = 0.0
    for it in db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).all():
        total_items += (it.unit_price or 0.0) * (it.qty or 0)
    order.total_items = round(total_items, 2)
    order.total_amount = round((order.total_items or 0.0) + (order.delivery_fee or 0.0) - (order.discount or 0.0), 2)


def _ensure_customer(db: Session, tenant: models.Tenant, wa_id: str) -> models.Customer:
    cust = (
        db.query(models.Customer)
        .filter(models.Customer.tenant_id == tenant.id, models.Customer.wa_id == wa_id)
        .first()
    )
    if not cust:
        cust = models.Customer(tenant_id=tenant.id, wa_id=wa_id)
        db.add(cust)
        db.flush()
    return cust


@router.post("")
def create_order(body: OrderCreate):
    with SessionLocal() as db:  # type: Session
        tenant = db.query(models.Tenant).filter(models.Tenant.name == settings.DEFAULT_TENANT_ID).first()
        if not tenant:
            tenant = models.Tenant(name=settings.DEFAULT_TENANT_ID)
            db.add(tenant)
            db.flush()
        cust = _ensure_customer(db, tenant, body.wa_id)
        order = models.Order(tenant_id=tenant.id, customer_id=cust.id, notes=body.notes)
        db.add(order)
        db.flush()

        mi = db.get(models.MenuItem, body.first_item.menu_item_id)
        if not mi or mi.tenant_id != tenant.id or not mi.available:
            raise HTTPException(status_code=400, detail="menu_item_unavailable")
        db.add(
            models.OrderItem(
                order_id=order.id,
                menu_item_id=mi.id,
                qty=body.first_item.qty,
                unit_price=mi.price,
                options=body.first_item.options,
            )
        )
        db.flush()  # ensure the new item is visible to queries
        _recalc_totals(db, order)
        db.commit()
        return {"order_id": order.id, "status": order.status.value, "total_amount": order.total_amount}


@router.patch("/{order_id}")
def update_order(order_id: int, op: Literal["add_item", "set_address", "confirm"], body: dict):
    with SessionLocal() as db:
        order = db.get(models.Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="order_not_found")
        if order.status not in (models.OrderStatus.draft, models.OrderStatus.pending_payment):
            raise HTTPException(status_code=400, detail="order_not_editable")

        tenant_id = order.tenant_id

        if op == "add_item":
            try:
                parsed = OrderAddItem(**body)
            except ValidationError as ve:
                raise HTTPException(status_code=422, detail=ve.errors())
            mi = db.get(models.MenuItem, parsed.menu_item_id)
            if not mi or mi.tenant_id != tenant_id or not mi.available:
                raise HTTPException(status_code=400, detail="menu_item_unavailable")
            db.add(
                models.OrderItem(
                    order_id=order.id,
                    menu_item_id=mi.id,
                    qty=parsed.qty,
                    unit_price=mi.price,
                    options=parsed.options,
                )
            )
            db.flush()
            _recalc_totals(db, order)

        elif op == "set_address":
            try:
                parsed = OrderSetAddress(**body)
            except ValidationError as ve:
                raise HTTPException(status_code=422, detail=ve.errors())
            # Persist as plain dict in JSON column
            order.delivery_address = parsed.address.model_dump()
            # calcular taxa se possível
            cep = parsed.address.cep
            district = parsed.address.district
            fee = delivery_fee_for(db, tenant_id, cep=cep, district=district)
            order.delivery_fee = fee
            db.flush()
            _recalc_totals(db, order)

        elif op == "confirm":
            try:
                parsed = OrderConfirm(**body)  # valida payload
            except ValidationError as ve:
                raise HTTPException(status_code=422, detail=ve.errors())
            # loja aberta?
            if not is_open_now(db, tenant_id):
                raise HTTPException(status_code=400, detail="store_closed")
            # requer endereço para confirmar
            if not order.delivery_address:
                raise HTTPException(status_code=400, detail="address_required")
            # recalcular por segurança e trocar status
            _recalc_totals(db, order)
            order.status = models.OrderStatus.pending_payment
        else:
            raise HTTPException(status_code=400, detail="invalid_op")

        db.add(order)
        db.commit()
        db.refresh(order)

        items = (
            db.query(models.OrderItem)
            .filter(models.OrderItem.order_id == order.id)
            .order_by(models.OrderItem.id)
            .all()
        )
        return {
            "order_id": order.id,
            "status": order.status.value,
            "total_items": order.total_items,
            "delivery_fee": order.delivery_fee,
            "total_amount": order.total_amount,
            "items": [
                {"id": it.id, "menu_item_id": it.menu_item_id, "qty": it.qty, "unit_price": it.unit_price, "options": it.options}
                for it in items
            ],
        }


@router.get("/{order_id}")
def get_order(order_id: int):
    with SessionLocal() as db:
        order = db.get(models.Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="order_not_found")
        items = (
            db.query(models.OrderItem)
            .filter(models.OrderItem.order_id == order.id)
            .order_by(models.OrderItem.id)
            .all()
        )
        return {
            "order_id": order.id,
            "status": order.status.value,
            "total_items": order.total_items,
            "delivery_fee": order.delivery_fee,
            "total_amount": order.total_amount,
            "delivery_address": order.delivery_address,
            "items": [
                {"id": it.id, "menu_item_id": it.menu_item_id, "qty": it.qty, "unit_price": it.unit_price, "options": it.options}
                for it in items
            ],
        }


@router.post("/{order_id}/pay")
def initiate_payment(order_id: int):
    """Gera um pagamento mock e retorna uma URL fake para simular provedor de pagamento.
    O consumidor deve chamar o webhook /webhooks/payments para marcar como 'paid'.
    """
    import uuid
    with SessionLocal() as db:
        order = db.get(models.Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="order_not_found")
        if not order.delivery_address:
            raise HTTPException(status_code=400, detail="address_required")
        db.flush()
        _recalc_totals(db, order)
        payment_id = str(uuid.uuid4())
        # URL fake de pagamento (em um provider real seria externo)
        payment_url = f"http://localhost:8000/webhooks/payments?order_id={order.id}&payment_id={payment_id}"
        return {"order_id": order.id, "payment_id": payment_id, "payment_url": payment_url}


@router.patch("/{order_id}/status")
def set_order_status(order_id: int, body: OrderSetStatus):
    """Atualiza status do pedido e envia notificação de texto via Celery (opcional).
    Transições válidas:
      draft -> canceled
      pending_payment -> paid | canceled
      paid -> in_kitchen | canceled
      in_kitchen -> out_for_delivery | canceled
      out_for_delivery -> delivered | canceled
    """
    with SessionLocal() as db:
        order = db.get(models.Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="order_not_found")

        current = order.status
        target = models.OrderStatus(body.status)

        # base matrix
        allowed: dict[models.OrderStatus, set[models.OrderStatus]] = {
            models.OrderStatus.draft: {models.OrderStatus.canceled},
            models.OrderStatus.pending_payment: {models.OrderStatus.paid, models.OrderStatus.canceled},
            models.OrderStatus.paid: {models.OrderStatus.in_kitchen, models.OrderStatus.canceled},
            models.OrderStatus.in_kitchen: {models.OrderStatus.out_for_delivery, models.OrderStatus.canceled},
            models.OrderStatus.out_for_delivery: {models.OrderStatus.delivered, models.OrderStatus.canceled},
            models.OrderStatus.delivered: set(),
            models.OrderStatus.canceled: set(),
        }

        # tenant flag: allow direct paid
        tenant = db.get(models.Tenant, order.tenant_id)
        allow_direct_paid = bool((tenant.settings_json or {}).get("allow_direct_paid")) if tenant else False

        if allow_direct_paid:
            # allow draft -> paid (with safeguards below)
            allowed.setdefault(models.OrderStatus.draft, set()).add(models.OrderStatus.paid)
            # allow operational states to accept late payment
            allowed.setdefault(models.OrderStatus.in_kitchen, set()).add(models.OrderStatus.paid)
            allowed.setdefault(models.OrderStatus.out_for_delivery, set()).add(models.OrderStatus.paid)

        if target not in allowed.get(current, set()):
            raise HTTPException(status_code=400, detail=f"invalid_transition:{current.value}->{target.value}")

        # Safeguards when jumping to paid directly
        if target is models.OrderStatus.paid and allow_direct_paid:
            # require address to compute delivery fee and finalize totals
            if not order.delivery_address:
                raise HTTPException(status_code=400, detail="address_required")
            # Recalc totals before setting paid
            db.flush()
            _recalc_totals(db, order)

        order.status = target
        db.add(order)
        db.commit()
        db.refresh(order)

        # Notificação simples (texto). Em produção, trocar por template apropriado.
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
                # dispara Celery de forma assíncrona
                task_send_text.delay(
                    tenant_id=order.tenant_id,
                    wa_id=customer.wa_id,
                    text=msg,
                    idempotency_key=f"order-status-{order.id}-{order.status.value}",
                )
        except Exception:
            # Evita falhar a API por causa de notificação; logs já cobertos pelo worker
            pass

        # Agendamentos automáticos com base nas SLAs do tenant (se auto_progress_enabled=true)
        try:
            tenant = db.get(models.Tenant, order.tenant_id)
            cfg = (tenant.settings_json if tenant else {}) or {}
            if cfg.get("auto_progress_enabled"):
                if order.status is models.OrderStatus.in_kitchen:
                    minutes = int(cfg.get("sla_entrega_min", 20))
                    countdown = max(0, minutes) * 60
                    set_status_task.apply_async(
                        kwargs={"order_id": order.id, "target_status": "out_for_delivery"}, countdown=countdown
                    )
                elif order.status is models.OrderStatus.out_for_delivery:
                    minutes = int(cfg.get("sla_finalizacao_min", 10))
                    countdown = max(0, minutes) * 60
                    set_status_task.apply_async(
                        kwargs={"order_id": order.id, "target_status": "delivered"}, countdown=countdown
                    )
        except Exception:
            pass

        return {"order_id": order.id, "status": order.status.value}
