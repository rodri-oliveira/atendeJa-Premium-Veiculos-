from __future__ import annotations
from sqlalchemy.orm import Session
from app.repositories import models


def ensure_tenant(db: Session, tenant_name: str) -> models.Tenant:
    tenant = db.query(models.Tenant).filter(models.Tenant.name == tenant_name).first()
    if not tenant:
        tenant = models.Tenant(name=tenant_name)
        db.add(tenant)
        db.flush()
    return tenant


def seed_basic_menu(db: Session, tenant: models.Tenant) -> None:
    if db.query(models.MenuItem).filter(models.MenuItem.tenant_id == tenant.id).count() > 0:
        return
    items = [
        models.MenuItem(tenant_id=tenant.id, name="Pizza Muçarela", category="pizza", price=39.9,
                        options={"sizes": ["P", "M", "G"]}),
        models.MenuItem(tenant_id=tenant.id, name="Pizza Calabresa", category="pizza", price=42.9,
                        options={"sizes": ["P", "M", "G"]}),
        models.MenuItem(tenant_id=tenant.id, name="X-Burger", category="lanche", price=22.0),
        models.MenuItem(tenant_id=tenant.id, name="Refrigerante Lata", category="bebida", price=7.0),
    ]
    db.add_all(items)


def seed_store_hours(db: Session, tenant: models.Tenant) -> None:
    if db.query(models.StoreHours).filter(models.StoreHours.tenant_id == tenant.id).count() > 0:
        return
    # Segunda a Domingo: 18:00 - 23:30
    for wd in range(7):
        db.add(models.StoreHours(tenant_id=tenant.id, weekday=wd, opens_at="18:00", closes_at="23:30"))


def seed_delivery_zones(db: Session, tenant: models.Tenant) -> None:
    if db.query(models.DeliveryZone).filter(models.DeliveryZone.tenant_id == tenant.id).count() > 0:
        return
    zones = [
        models.DeliveryZone(tenant_id=tenant.id, name="Centro", fee=5.0, criteria={"cep_prefix": ["010", "011"]}),
        models.DeliveryZone(tenant_id=tenant.id, name="Bairro A", fee=8.0, criteria={"cep_prefix": ["012", "013"]}),
    ]
    db.add_all(zones)


def seed_all(db: Session, tenant_name: str) -> None:
    tenant = ensure_tenant(db, tenant_name)
    seed_basic_menu(db, tenant)
    seed_store_hours(db, tenant)
    seed_delivery_zones(db, tenant)
    db.commit()
