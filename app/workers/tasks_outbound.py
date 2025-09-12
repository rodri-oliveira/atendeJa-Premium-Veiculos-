from __future__ import annotations
import random
import time
import structlog
from celery import Task
from app.core.config import settings
from app.domain.messaging.wa_client import get_wa_client
from app.domain.policies import within_business_hours
from app.repositories.db import SessionLocal
from app.repositories import models
from .celery_app import celery

log = structlog.get_logger()


class TransientSendError(Exception):
    pass


def _should_retry(status_code: int) -> bool:
    return status_code >= 500


def _backoff(retry_count: int) -> float:
    base = 2 ** max(0, retry_count)
    jitter = random.uniform(0, 0.2 * base)
    return min(30.0, base + jitter)


@celery.task(name="outbound.send_text", bind=True, max_retries=5)
def send_text(self: Task, tenant_id: str, to_wa_id: str, text: str, idempotency_key: str | None = None) -> dict:
    # Respect business hours (simple policy for now)
    if not within_business_hours():
        log.info("outbound_skipped_off_hours", tenant_id=tenant_id, to=to_wa_id)
        return {"status": "scheduled"}

    with SessionLocal() as db:
        # Resolve tenant by name (DEFAULT_TENANT_ID currently mapped to name)
        tenant = db.query(models.Tenant).filter(models.Tenant.name == tenant_id).first()
        if tenant is None:
            tenant = models.Tenant(name=tenant_id)
            db.add(tenant)
            db.flush()

        # Idempotency guard
        if idempotency_key:
            existing = (
                db.query(models.Message)
                .filter(
                    models.Message.tenant_id == tenant.id,
                    models.Message.idempotency_key == idempotency_key,
                )
                .first()
            )
            if existing is not None:
                log.info("outbound_idempotent_skip", tenant_id=tenant_id, key=idempotency_key)
                return {"status": "duplicate"}

        # Create conversation on demand (outbound-only)
        contact = (
            db.query(models.Contact)
            .filter(models.Contact.tenant_id == tenant.id, models.Contact.wa_id == to_wa_id)
            .first()
        )
        if contact is None:
            contact = models.Contact(tenant_id=tenant.id, wa_id=to_wa_id)
            db.add(contact)
            db.flush()

        convo = (
            db.query(models.Conversation)
            .filter(
                models.Conversation.tenant_id == tenant.id,
                models.Conversation.contact_id == contact.id,
                models.Conversation.status != models.ConversationStatus.closed,
            )
            .order_by(models.Conversation.id.desc())
            .first()
        )
        if convo is None:
            convo = models.Conversation(tenant_id=tenant.id, contact_id=contact.id)
            db.add(convo)
            db.flush()

        # Record message as queued
        msg = models.Message(
            tenant_id=tenant.id,
            conversation_id=convo.id,
            direction=models.MessageDirection.outbound,
            type="text",
            payload={"text": text},
            status="queued",
            idempotency_key=idempotency_key,
        )
        db.add(msg)
        db.commit()

    client = get_wa_client()
    try:
        resp = client.send_text(to_wa_id=to_wa_id, text=text)
    except Exception as e:  # Consider HTTP status in logs handled inside client
        # Retry on transient errors; here we assume any exception is transient for simplicity
        retry_no = self.request.retries
        delay = _backoff(retry_no)
        log.warning("outbound_retry", retries=retry_no + 1, delay=delay)
        raise self.retry(exc=TransientSendError(str(e)), countdown=delay)

    # Mark as sent
    with SessionLocal() as db:
        last = (
            db.query(models.Message)
            .filter(models.Message.tenant_id == tenant.id)
            .order_by(models.Message.id.desc())
            .first()
        )
        if last is not None and last.status == "queued":
            last.status = "sent"
            last.payload = {**(last.payload or {}), "wa_response": resp}
            db.add(last)
            db.commit()

    return {"status": "sent", "response": resp}


@celery.task(name="outbound.send_template", bind=True, max_retries=5)
def send_template(
    self: Task,
    tenant_id: str,
    to_wa_id: str,
    template_name: str,
    language_code: str = "pt_BR",
    components: list[dict] | None = None,
    idempotency_key: str | None = None,
) -> dict:
    # Template messages podem ser enviadas fora do horário, mas mantemos a mesma política por simplicidade
    if not within_business_hours():
        log.info("outbound_template_skipped_off_hours", tenant_id=tenant_id, to=to_wa_id)
        return {"status": "scheduled"}

    with SessionLocal() as db:
        tenant = db.query(models.Tenant).filter(models.Tenant.name == tenant_id).first()
        if tenant is None:
            tenant = models.Tenant(name=tenant_id)
            db.add(tenant)
            db.flush()

        if idempotency_key:
            existing = (
                db.query(models.Message)
                .filter(
                    models.Message.tenant_id == tenant.id,
                    models.Message.idempotency_key == idempotency_key,
                )
                .first()
            )
            if existing is not None:
                log.info("outbound_template_idempotent_skip", tenant_id=tenant_id, key=idempotency_key)
                return {"status": "duplicate"}

        contact = (
            db.query(models.Contact)
            .filter(models.Contact.tenant_id == tenant.id, models.Contact.wa_id == to_wa_id)
            .first()
        )
        if contact is None:
            contact = models.Contact(tenant_id=tenant.id, wa_id=to_wa_id)
            db.add(contact)
            db.flush()

        convo = (
            db.query(models.Conversation)
            .filter(
                models.Conversation.tenant_id == tenant.id,
                models.Conversation.contact_id == contact.id,
                models.Conversation.status != models.ConversationStatus.closed,
            )
            .order_by(models.Conversation.id.desc())
            .first()
        )
        if convo is None:
            convo = models.Conversation(tenant_id=tenant.id, contact_id=contact.id)
            db.add(convo)
            db.flush()

        msg = models.Message(
            tenant_id=tenant.id,
            conversation_id=convo.id,
            direction=models.MessageDirection.outbound,
            type="template",
            payload={
                "template": template_name,
                "language_code": language_code,
                "components": components or [],
            },
            status="queued",
            idempotency_key=idempotency_key,
        )
        db.add(msg)
        db.commit()

    client = get_wa_client()
    try:
        resp = client.send_template(
            to_wa_id=to_wa_id,
            template_name=template_name,
            language_code=language_code,
            components=components,
        )
    except Exception as e:
        retry_no = self.request.retries
        delay = _backoff(retry_no)
        log.warning("outbound_template_retry", retries=retry_no + 1, delay=delay)
        raise self.retry(exc=TransientSendError(str(e)), countdown=delay)

    with SessionLocal() as db:
        last = (
            db.query(models.Message)
            .filter(models.Message.tenant_id == tenant.id)
            .order_by(models.Message.id.desc())
            .first()
        )
        if last is not None and last.status == "queued":
            last.status = "sent"
            last.payload = {**(last.payload or {}), "wa_response": resp}
            db.add(last)
            db.commit()

    return {"status": "sent", "response": resp}
