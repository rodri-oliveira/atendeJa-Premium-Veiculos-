from fastapi.testclient import TestClient
from app.main import app
from app.repositories.db import SessionLocal
from app.repositories import models
from app.core.config import settings


def _ensure_default_tenant_and_menu(price: float = 10.0) -> int:
    """Ensure a default tenant and a menu item exist; return menu_item_id."""
    with SessionLocal() as db:
        tenant_name = getattr(settings, "DEFAULT_TENANT_ID", "default")
        tenant = db.query(models.Tenant).filter(models.Tenant.name == tenant_name).first()
        if not tenant:
            tenant = models.Tenant(name=tenant_name)
            db.add(tenant)
            db.flush()

        # create a simple item
        mi = models.MenuItem(tenant_id=tenant.id, name="Test Item", category="pizza", price=price, available=True)
        db.add(mi)
        db.flush()
        db.commit()
        return mi.id


def test_reorder_creates_relation_and_child_list():
    client = TestClient(app)

    menu_id = _ensure_default_tenant_and_menu(price=10.0)

    # create base order
    resp = client.post(
        "/orders",
        json={
            "wa_id": "5511999999999",
            "first_item": {"menu_item_id": menu_id, "qty": 1, "options": {"size": "M"}},
            "notes": "pedido base",
        },
    )
    assert resp.status_code == 200
    base_id = resp.json()["order_id"]

    # set address to allow confirm
    resp = client.patch(
        f"/orders/{base_id}?op=set_address",
        json={
            "address": {
                "street": "Rua A",
                "number": "123",
                "district": "Centro",
                "city": "São Paulo",
                "state": "SP",
                "cep": "01312-000",
            }
        },
    )
    assert resp.status_code == 200

    # confirm (goes to pending_payment)
    resp = client.patch(f"/orders/{base_id}?op=confirm", json={"confirm": True})
    assert resp.status_code == 200

    # reorder from base
    resp = client.post(f"/orders/{base_id}/reorder", json={"include_address": True, "notes": "reorder"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_order_id"] == base_id
    new_id = body["order_id"]
    assert new_id != base_id

    # relation of child must point to base
    resp = client.get(f"/orders/{new_id}/relation")
    assert resp.status_code == 200
    assert resp.json() == {"order_id": new_id, "source_order_id": base_id}

    # relation of base must be null
    resp = client.get(f"/orders/{base_id}/relation")
    assert resp.status_code == 200
    assert resp.json() == {"order_id": base_id, "source_order_id": None}

    # list reorders from base must include the child
    resp = client.get(f"/orders/{base_id}/reorders")
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()]
    assert new_id in ids


def test_reorder_uses_current_menu_price():
    client = TestClient(app)

    menu_id = _ensure_default_tenant_and_menu(price=10.0)

    # create base order with price 10.0
    resp = client.post(
        "/orders",
        json={
            "wa_id": "5511888888888",
            "first_item": {"menu_item_id": menu_id, "qty": 1},
        },
    )
    assert resp.status_code == 200
    base_id = resp.json()["order_id"]

    # bump current menu price to 12.0
    with SessionLocal() as db:
        mi = db.get(models.MenuItem, menu_id)
        mi.price = 12.0
        db.add(mi)
        db.commit()

    # reorder should use 12.0 now
    resp = client.post(f"/orders/{base_id}/reorder", json={"include_address": False})
    assert resp.status_code == 200
    new_id = resp.json()["order_id"]

    # fetch new order and assert totals use updated price
    resp = client.get(f"/orders/{new_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_items"] == 12.0


def test_reorder_skips_unavailable_items():
    client = TestClient(app)

    # create two items
    id_a = _ensure_default_tenant_and_menu(price=10.0)
    id_b = _ensure_default_tenant_and_menu(price=7.0)

    # create base order with item A
    resp = client.post(
        "/orders",
        json={
            "wa_id": "5511777777777",
            "first_item": {"menu_item_id": id_a, "qty": 1},
        },
    )
    assert resp.status_code == 200
    base_id = resp.json()["order_id"]

    # add item B
    resp = client.patch(f"/orders/{base_id}?op=add_item", json={"menu_item_id": id_b, "qty": 1})
    assert resp.status_code == 200

    # make item B unavailable before reorder
    with SessionLocal() as db:
        mi_b = db.get(models.MenuItem, id_b)
        mi_b.available = False
        db.add(mi_b)
        db.commit()

    # reorder should copy only available item A (10.0)
    resp = client.post(f"/orders/{base_id}/reorder", json={"include_address": False})
    assert resp.status_code == 200
    new_id = resp.json()["order_id"]
    resp = client.get(f"/orders/{new_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_items"] == 10.0


def test_reorder_without_address_keeps_zero_delivery_fee():
    client = TestClient(app)
    menu_id = _ensure_default_tenant_and_menu(price=9.0)

    # base order
    resp = client.post(
        "/orders",
        json={
            "wa_id": "5511666666666",
            "first_item": {"menu_item_id": menu_id, "qty": 1},
        },
    )
    assert resp.status_code == 200
    base_id = resp.json()["order_id"]

    # reorder without address
    resp = client.post(f"/orders/{base_id}/reorder", json={"include_address": False})
    assert resp.status_code == 200
    new_id = resp.json()["order_id"]
    resp = client.get(f"/orders/{new_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["delivery_fee"] == 0


def test_get_orders_filters_by_status_and_search():
    client = TestClient(app)
    menu_id = _ensure_default_tenant_and_menu(price=5.0)

    # create two draft orders for different wa_ids
    resp1 = client.post(
        "/orders",
        json={"wa_id": "550000000001", "first_item": {"menu_item_id": menu_id, "qty": 1}},
    )
    assert resp1.status_code == 200
    resp2 = client.post(
        "/orders",
        json={"wa_id": "551234567890", "first_item": {"menu_item_id": menu_id, "qty": 1}},
    )
    assert resp2.status_code == 200

    # filter by status=draft should return at least these orders
    resp = client.get("/orders", params={"status": "draft", "limit": 100})
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()]
    assert resp1.json()["order_id"] in ids
    assert resp2.json()["order_id"] in ids

    # search by wa_id should restrict results
    resp = client.get("/orders", params={"search": "551234567890", "limit": 100})
    assert resp.status_code == 200
    rows = resp.json()
    # all rows must belong to customer with wa_id matched; we check at least one and that not empty
    assert rows, "search should return at least one row"
