from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.repositories.db import SessionLocal
from app.repositories.models import Conversation, ConversationStatus, Message, Contact, Tenant
import structlog
from app.core.config import settings
from app.workers.tasks_outbound import send_text as task_send_text
from app.workers.tasks_outbound import send_template as task_send_template
from app.workers.tasks_orders import check_sla_alerts as task_check_sla_alerts

router = APIRouter()
log = structlog.get_logger()


class HandoffAction(BaseModel):
    action: str  # "human" | "bot"


@router.post("/conversations/{conversation_id}/handoff")
def set_handoff(conversation_id: int, body: HandoffAction):
    with SessionLocal() as db:  # type: Session
        convo = db.get(Conversation, conversation_id)
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if body.action == "human":
            convo.status = ConversationStatus.human_handoff
        elif body.action == "bot":
            convo.status = ConversationStatus.active_bot
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'human' or 'bot'.")
        db.add(convo)
        db.commit()
        log.info("handoff_changed", conversation_id=conversation_id, status=convo.status.value)
        return {"conversation_id": conversation_id, "status": convo.status.value}


class HumanSendMessage(BaseModel):
    conversation_id: int
    text: str


@router.post("/messages/send-human")
def send_message_as_human(body: HumanSendMessage):
    # Placeholder: neste momento apenas registra. Em seguida integraremos ao envio real.
    log.info(
        "human_message_send_requested",
        conversation_id=body.conversation_id,
        text=body.text,
    )
    return {"queued": True}


class AdminSendText(BaseModel):
    wa_id: str
    text: str
    idempotency_key: str | None = None


@router.post("/send-text")
def admin_send_text(body: AdminSendText):
    """Enfileira envio de texto via WhatsApp Cloud API.
    Usa o tenant padrão enquanto não há multi-tenant no admin.
    """
    tenant_id = settings.DEFAULT_TENANT_ID
    async_result = task_send_text.delay(tenant_id, body.wa_id, body.text, body.idempotency_key)
    log.info("admin_send_text_enqueued", wa_id=body.wa_id, task_id=async_result.id)
    return {"queued": True, "task_id": async_result.id}


class AdminSendTemplate(BaseModel):
    wa_id: str
    template_name: str
    language_code: str = "pt_BR"
    components: list[dict] | None = None
    idempotency_key: str | None = None


@router.post("/send-template")
def admin_send_template(body: AdminSendTemplate):
    tenant_id = settings.DEFAULT_TENANT_ID
    async_result = task_send_template.delay(
        tenant_id,
        body.wa_id,
        body.template_name,
        body.language_code,
        body.components,
        body.idempotency_key,
    )
    log.info("admin_send_template_enqueued", wa_id=body.wa_id, template=body.template_name, task_id=async_result.id)
    return {"queued": True, "task_id": async_result.id}


@router.get("/conversations")
def list_conversations(wa_id: str, limit: int = 50):
    """Lista conversas recentes para um wa_id (tenant padrão)."""
    with SessionLocal() as db:  # type: Session
        tenant = db.query(Tenant).filter(Tenant.name == settings.DEFAULT_TENANT_ID).first()
        if not tenant:
            return []
        contact = (
            db.query(Contact)
            .filter(Contact.tenant_id == tenant.id, Contact.wa_id == wa_id)
            .first()
        )
        if not contact:
            return []
        convos = (
            db.query(Conversation)
            .filter(Conversation.tenant_id == tenant.id, Conversation.contact_id == contact.id)
            .order_by(Conversation.id.desc())
            .limit(max(1, min(limit, 200)))
            .all()
        )
        return [
            {
                "id": c.id,
                "status": c.status.value,
                "contact_id": c.contact_id,
                "tenant_id": c.tenant_id,
            }
            for c in convos
        ]


@router.get("/messages")
def list_messages(wa_id: str, limit: int = 50):
    """Lista mensagens recentes para um wa_id (tenant padrão)."""
    with SessionLocal() as db:  # type: Session
        tenant = db.query(Tenant).filter(Tenant.name == settings.DEFAULT_TENANT_ID).first()
        if not tenant:
            return []
        contact = (
            db.query(Contact)
            .filter(Contact.tenant_id == tenant.id, Contact.wa_id == wa_id)
            .first()
        )
        if not contact:
            return []
        # mensagens de todas as conversas deste contato
        conv_ids = (
            db.query(Conversation.id)
            .filter(Conversation.tenant_id == tenant.id, Conversation.contact_id == contact.id)
            .subquery()
        )
        msgs = (
            db.query(Message)
            .filter(Message.tenant_id == tenant.id, Message.conversation_id.in_(conv_ids))
            .order_by(Message.id.desc())
            .limit(max(1, min(limit, 200)))
            .all()
        )
        out = []
        for m in msgs:
            out.append(
                {
                    "id": m.id,
                    "conversation_id": m.conversation_id,
                    "direction": m.direction.value,
                    "type": m.type,
                    "status": m.status,
                    "payload": m.payload,
                    "created_at": getattr(m, "created_at", None),
                }
            )
        return out


class TenantSettingsUpdate(BaseModel):
    allow_direct_paid: bool | None = None
    auto_progress_enabled: bool | None = None
    sla_preparo_min: int | None = None
    sla_entrega_min: int | None = None
    sla_finalizacao_min: int | None = None
    timezone: str | None = None
    # WhatsApp templates
    template_lang: str | None = None  # ex.: "pt_BR"
    template_confirm: str | None = None
    template_paid: str | None = None
    template_in_kitchen: str | None = None
    template_out_for_delivery: str | None = None
    template_delivered: str | None = None
    # SLA alerts (operação)
    alerts_enabled: bool | None = None
    alerts_channel: str | None = None  # "whatsapp" | "log"
    alerts_ops_wa_id: str | None = None  # número WhatsApp do operador/gestor


@router.patch("/tenant-settings")
def update_tenant_settings(body: TenantSettingsUpdate):
    """Atualiza o settings_json do tenant padrão.
    Envie apenas os campos que deseja alterar. Exemplo de body:
    {
      "allow_direct_paid": true,
      "sla_preparo_min": 10,
      "sla_entrega_min": 20,
      "timezone": "America/Sao_Paulo"
    }
    """
    with SessionLocal() as db:  # type: Session
        tenant = db.query(Tenant).filter(Tenant.name == settings.DEFAULT_TENANT_ID).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="tenant_not_found")
        cfg = dict(tenant.settings_json or {})
        updates = body.model_dump(exclude_unset=True)
        cfg.update({k: v for k, v in updates.items() if v is not None})
        tenant.settings_json = cfg
        db.add(tenant)
        db.commit()
        return {"tenant": tenant.name, "settings_json": tenant.settings_json}


@router.post("/run-sla-check")
def run_sla_check_now():
    """Dispara uma verificação de atrasos por SLA (execução assíncrona)."""
    async_result = task_check_sla_alerts.delay()
    log.info("sla_check_enqueued", task_id=async_result.id)
    return {"queued": True, "task_id": async_result.id}
