from __future__ import annotations
from datetime import datetime, time
from typing import Optional
from sqlalchemy.orm import Session
from app.repositories import models
from zoneinfo import ZoneInfo


def _parse_hhmm(s: str) -> time:
    hh, mm = s.split(":")
    return time(int(hh), int(mm))


def is_open_now(db: Session, tenant_id: int, when: Optional[datetime] = None) -> bool:
    """Return True if store is open at 'when'.
    - Usa timezone do tenant (models.Tenant.timezone) para calcular dia/hora local.
    - Suporta faixas que passam da meia-noite (ex.: 18:00-02:00).
    """
    # resolve timezone do tenant
    tenant = db.get(models.Tenant, tenant_id)
    tzname = getattr(tenant, "timezone", None) or "America/Sao_Paulo"
    tz = ZoneInfo(tzname)
    when = (when or datetime.utcnow()).astimezone(tz)
    weekday = when.weekday()  # 0=Mon .. 6=Sun (no timezone local)
    sh = (
        db.query(models.StoreHours)
        .filter(models.StoreHours.tenant_id == tenant_id, models.StoreHours.weekday == weekday)
        .first()
    )
    if not sh:
        return False
    opens = _parse_hhmm(sh.opens_at)
    closes = _parse_hhmm(sh.closes_at)
    now_t = time(when.hour, when.minute)
    # Suporte a horário que passa de meia-noite: se closes < opens, então janela é [opens..23:59] U [00:00..closes]
    if closes < opens:
        return (now_t >= opens) or (now_t <= closes)
    return opens <= now_t <= closes


def delivery_fee_for(db: Session, tenant_id: int, cep: Optional[str] = None, district: Optional[str] = None) -> float:
    """Resolve delivery fee by simple criteria matching order:
    1) district exact match if provided
    2) cep_prefix (first 3 digits) if provided via criteria {"cep_prefix": ["013", ...]}
    Returns 0.0 if no match.
    """
    zones = db.query(models.DeliveryZone).filter(models.DeliveryZone.tenant_id == tenant_id).all()
    if district:
        for z in zones:
            if z.name.lower() == district.lower():
                return float(z.fee or 0.0)
    if cep:
        prefix = cep.replace("-", "").strip()[:3]
        for z in zones:
            crit = z.criteria or {}
            prefixes = crit.get("cep_prefix") or []
            if prefix and prefix in prefixes:
                return float(z.fee or 0.0)
    return 0.0
