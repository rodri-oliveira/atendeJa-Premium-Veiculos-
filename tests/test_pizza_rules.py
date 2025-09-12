from datetime import datetime
from app.domain.pizza.rules import is_open_now, delivery_fee_for
from app.domain.pizza.seeds import seed_all
from app.repositories.db import SessionLocal, engine
from app.repositories.models import Base
from app.core.config import settings
from sqlalchemy import text


def setup_module(module):
    # create tables for tests (APP_ENV=test skips app startup create_all)
    Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    try:
        seed_all(s, settings.DEFAULT_TENANT_ID)
    finally:
        s.close()


def teardown_module(module):
    # optional: don't drop tables to allow reuse; keep stateful for speed
    pass


def test_is_open_now_true_within_range():
    s = SessionLocal()
    try:
        # Thursday 20:00 (within 18:00-23:30)
        ts = datetime(2025, 9, 11, 20, 0, 0)
        tenant_id = s.execute(text("select id from tenants where name = :n"), {"n": settings.DEFAULT_TENANT_ID}).fetchone()[0]
        assert is_open_now(s, tenant_id, when=ts) is True
    finally:
        s.close()


def test_delivery_fee_by_prefix_and_district():
    s = SessionLocal()
    try:
        tenant_id = s.execute(text("select id from tenants where name = :n"), {"n": settings.DEFAULT_TENANT_ID}).fetchone()[0]
        fee1 = delivery_fee_for(s, tenant_id, cep="01312-000")
        assert fee1 in (8.0, 8, 8.0)
        fee2 = delivery_fee_for(s, tenant_id, district="Centro")
        assert fee2 in (5.0, 5, 5.0)
    finally:
        s.close()
