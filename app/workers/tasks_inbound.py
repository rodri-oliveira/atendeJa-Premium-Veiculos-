from __future__ import annotations
from datetime import timedelta
import json
import structlog
import redis
from app.core.config import settings
from .celery_app import celery

log = structlog.get_logger()

# Aggregation settings (can be made per-tenant later)
AGG_WINDOW_SECONDS = 2
MAX_COMPOSE_LEN = 1200


def _redis() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def _agg_key(tenant_id: str, wa_id: str) -> str:
    return f"agg:{tenant_id}:{wa_id}"


def _compose(prev: str, new: str) -> str:
    if not prev:
        return new
    # Add space if needed
    sep = "" if prev.endswith((" ", "\n")) else " "
    out = (prev + sep + new).strip()
    if len(out) > MAX_COMPOSE_LEN:
        return out[:MAX_COMPOSE_LEN]
    return out


@celery.task(name="inbound.buffer")
def buffer_incoming_message(tenant_id: str, wa_id: str, text: str, raw_event: dict) -> None:
    r = _redis()
    key = _agg_key(tenant_id, wa_id)
    pipe = r.pipeline()
    # Compose buffered text
    existing = r.hget(key, "text") or ""
    composed = _compose(existing, text)
    pipe.hset(key, mapping={"text": composed, "raw": json.dumps(raw_event)})
    # Set/refresh TTL as aggregation window
    pipe.expire(key, AGG_WINDOW_SECONDS)
    pipe.execute()
    log.info("inbound_buffered", key=key, len=len(composed))
    # Schedule flush after window using countdown; idempotent by key
    flush_incoming_message.apply_async((tenant_id, wa_id), countdown=AGG_WINDOW_SECONDS)


@celery.task(name="inbound.flush")
def flush_incoming_message(tenant_id: str, wa_id: str) -> None:
    r = _redis()
    key = _agg_key(tenant_id, wa_id)
    # If key still exists, window expired and we can flush
    if not r.exists(key):
        return
    data = r.hgetall(key)
    text = data.get("text") or ""
    raw = data.get("raw")
    # Delete first to avoid duplicate flushes
    r.delete(key)
    log.info("inbound_flushed", key=key, text_len=len(text))
    # TODO: normalize raw event, resolve/create contact/conversation
    # If conversation is in human_handoff, just persist; else, call state machine
    # For now, just log.
    return
