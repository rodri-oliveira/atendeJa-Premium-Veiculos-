from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.db import SessionLocal
from app.repositories import models
from app.core.config import settings
from app.workers.tasks_orders import check_sla_alerts, set_status_task


def _get_default_tenant(db):
    t = db.query(models.Tenant).filter(models.Tenant.name == settings.DEFAULT_TENANT_ID).first()
    if not t:
        t = models.Tenant(name=settings.DEFAULT_TENANT_ID)
        db.add(t)
        db.flush()
    return t


def _ensure_customer(db, tenant, wa_id="5599999999999"):
    c = (
        db.query(models.Customer)
        .filter(models.Customer.tenant_id == tenant.id, models.Customer.wa_id == wa_id)
        .first()
    )
    if not c:
        c = models.Customer(tenant_id=tenant.id, wa_id=wa_id, name="Tester")
        db.add(c)
        db.flush()
    return c


def _ensure_menu(db, tenant, price=10.0):
    mi = models.MenuItem(tenant_id=tenant.id, name="Item", category="pizza", price=price, available=True)
    db.add(mi)
    db.flush()
    return mi


def test_sla_alerts_uses_status_event_timestamp():
    """Creates an order and a status event in the past so it exceeds SLA; then runs task and expects alert."""
    client = TestClient(app)
    with SessionLocal() as db:
        tenant = _get_default_tenant(db)
        # enable alerts, simple thresholds
        cfg = dict(tenant.settings_json or {})
        cfg.update({
            "alerts_enabled": True,
            "alerts_channel": "log",
            "sla_preparo_min": 1,
            "sla_entrega_min": 1,
            "sla_finalizacao_min": 1,
        })
        tenant.settings_json = cfg
        db.add(tenant)
        db.flush()

        # create customer and order in 'paid'
        cust = _ensure_customer(db, tenant)
        order = models.Order(tenant_id=tenant.id, customer_id=cust.id, status=models.OrderStatus.paid)
        db.add(order)
        db.flush()
        # status event: paid happened 3 minutes ago (exceeds sla_preparo_min=1)
        ev = models.OrderStatusEvent(order_id=order.id, from_status="pending_payment", to_status="paid",
                                     created_at=datetime.utcnow() - timedelta(minutes=3))
        db.add(ev)
        db.commit()
        oid = order.id

    # run task
    res = check_sla_alerts()
    assert res["ok"] is True
    assert oid in res["alerted_orders"], f"Expected order {oid} to be alerted"


def test_templates_send_and_fallback(monkeypatch):
    """When template configured, use send_template; otherwise fallback to send_text."""
    calls_template = []
    calls_text = []

    class DummyTemplate:
        def delay(self, **kwargs):
            calls_template.append(kwargs)

    class DummyText:
        def delay(self, **kwargs):
            calls_text.append(kwargs)

    # monkeypatch the outbound tasks
    import app.workers.tasks_orders as tasks_mod
    monkeypatch.setattr(tasks_mod, "task_send_template", DummyTemplate())
    monkeypatch.setattr(tasks_mod, "task_send_text", DummyText())

    with SessionLocal() as db:
        tenant = _get_default_tenant(db)
        # configure only in_kitchen template
        cfg = dict(tenant.settings_json or {})
        cfg.update({
            "template_lang": "pt_BR",
            "template_in_kitchen": "pedido_em_preparo",
            # others not set => fallback to text
        })
        tenant.settings_json = cfg
        db.add(tenant)
        db.flush()

        cust = _ensure_customer(db, tenant, wa_id="5591111111111")
        order = models.Order(tenant_id=tenant.id, customer_id=cust.id, status=models.OrderStatus.paid)
        db.add(order)
        db.commit()
        db.refresh(order)
        oid = order.id

    # transition to in_kitchen -> should use template
    res = set_status_task(order_id=oid, target_status="in_kitchen")
    assert res["ok"] is True
    assert any(c.get("template_name") == "pedido_em_preparo" for c in calls_template)

    # transition to out_for_delivery -> no template configured, fallback to text
    res = set_status_task(order_id=oid, target_status="out_for_delivery")
    assert res["ok"] is True
    assert any("text" in c for c in calls_text)
