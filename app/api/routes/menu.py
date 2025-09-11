from __future__ import annotations
from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from app.repositories.db import SessionLocal
from app.repositories import models
from app.core.config import settings

router = APIRouter()


@router.get("")
def list_menu(category: str | None = Query(default=None), only_available: bool = True):
    """Lista itens do cardápio do tenant padrão, opcionalmente filtrando por categoria.
    """
    with SessionLocal() as db:  # type: Session
        tenant = db.query(models.Tenant).filter(models.Tenant.name == settings.DEFAULT_TENANT_ID).first()
        if not tenant:
            return []
        q = db.query(models.MenuItem).filter(models.MenuItem.tenant_id == tenant.id)
        if category:
            q = q.filter(models.MenuItem.category == category)
        if only_available:
            q = q.filter(models.MenuItem.available == True)  # noqa: E712
        items = q.order_by(models.MenuItem.category, models.MenuItem.name).all()
        out = []
        for it in items:
            out.append(
                {
                    "id": it.id,
                    "name": it.name,
                    "category": it.category,
                    "price": it.price,
                    "available": it.available,
                    "options": it.options,
                }
            )
        return out
