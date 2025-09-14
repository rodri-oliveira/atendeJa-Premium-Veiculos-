from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from app.core.config import settings
import structlog
import hmac
import hashlib
from app.repositories.db import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.repositories import models as core_models
from app.domain.realestate import models as re_models
 
from pydantic import BaseModel
from typing import Literal
 

router = APIRouter()
log = structlog.get_logger()


@router.get("")
async def verify(
    request: Request,
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
):
    """
    Meta sends the verification GET with query params using the 'hub.' prefix.
    Example: /webhook?hub.mode=subscribe&hub.challenge=123&hub.verify_token=xxx
    """
    if hub_verify_token != settings.WA_VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid verify token")
    # Return the challenge as plain text
    return PlainTextResponse(hub_challenge or "")


@router.post("")
async def receive(request: Request):
    # Read raw body to handle different encodings safely
    import json  # local import to avoid global overhead
    body_bytes: bytes = await request.body()
    # Optional: validate HMAC from Meta if secret configured
    try:
        secret = settings.WA_WEBHOOK_SECRET
    except Exception:
        secret = ""
    signature = request.headers.get("x-hub-signature-256")
    if secret:
        if not signature or not signature.startswith("sha256="):
            log.error("webhook_hmac_missing_or_malformed")
            return {"received": True, "error": "invalid_signature"}
        expected = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        provided = signature.split("=", 1)[1]
        if not hmac.compare_digest(expected, provided):
            log.error("webhook_hmac_mismatch")
            return {"received": True, "error": "invalid_signature"}
    payload = None
    if not body_bytes:
        log.error("webhook_json_error", error="empty body")
        return {"received": True, "error": "invalid_json"}
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            payload = json.loads(body_bytes.decode(enc))
            break
        except Exception:  # noqa: BLE001
            payload = None
            continue
    if payload is None:
        try:
            # As a last resort, try FastAPI's parser
            payload = await request.json()
        except Exception as e:  # noqa: BLE001
            log.error("webhook_json_error", error=str(e))
            return {"received": True, "error": "invalid_json"}

    log.info("webhook_received", payload=payload)

    # Extrair texto e wa_id do payload do WhatsApp
    try:
        entries = payload.get("entry", []) or []
        for entry in entries:
            changes = entry.get("changes", []) or []
            for change in changes:
                value = change.get("value", {}) or {}
                messages = value.get("messages", []) or []
                contacts = value.get("contacts", []) or []
                wa_id = None
                if contacts:
                    wa_id = contacts[0].get("wa_id") or contacts[0].get("wa_id")
                for msg in messages:
                    if not wa_id:
                        wa_id = msg.get("from")
                    if msg.get("type") != "text":
                        continue
                    text_in = (msg.get("text", {}) or {}).get("body", "").strip()
                    if not text_in:
                        continue

                    # Processar funil imobiliário sincronamente (MVP)
                    with SessionLocal() as db:
                        resp_text = _process_realestate_funnel(db, tenant_name=settings.DEFAULT_TENANT_ID, wa_id=wa_id or "unknown", user_text=text_in)
                        # Para MVP, apenas logamos a resposta. Em produção, enviaríamos via WhatsApp API.
                        log.info("bot_reply", wa_id=wa_id, reply=resp_text)
        return {"received": True}
    except Exception as e:  # noqa: BLE001
        log.error("webhook_process_error", error=str(e))
        return {"received": True, "error": "processing"}


class PaymentEvent(BaseModel):
    order_id: int
    payment_id: str | None = None
    status: Literal["paid"]


 
def _normalize_text(s: str) -> str:
    return s.strip().lower()


def _ensure_tenant(db: Session, tenant_name: str) -> core_models.Tenant:
    stmt = select(core_models.Tenant).where(core_models.Tenant.name == tenant_name)
    tenant = db.execute(stmt).scalar_one_or_none()
    if not tenant:
        tenant = core_models.Tenant(name=tenant_name)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


def _ensure_contact(db: Session, tenant_id: int, wa_id: str) -> core_models.Contact:
    stmt = select(core_models.Contact).where(
        core_models.Contact.tenant_id == tenant_id,
        core_models.Contact.wa_id == wa_id,
    )
    c = db.execute(stmt).scalar_one_or_none()
    if not c:
        c = core_models.Contact(tenant_id=tenant_id, wa_id=wa_id)
        db.add(c)
        db.commit()
        db.refresh(c)
    return c


def _ensure_conversation(db: Session, tenant_id: int, contact_id: int) -> core_models.Conversation:
    stmt = (
        select(core_models.Conversation)
        .where(
            core_models.Conversation.tenant_id == tenant_id,
            core_models.Conversation.contact_id == contact_id,
            core_models.Conversation.status == core_models.ConversationStatus.active_bot,
        )
        .order_by(core_models.Conversation.id.desc())
    )
    conv = db.execute(stmt).scalar_one_or_none()
    if not conv:
        conv = core_models.Conversation(
            tenant_id=tenant_id,
            contact_id=contact_id,
            status=core_models.ConversationStatus.active_bot,
            last_state=None,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


def _record_event(db: Session, conversation_id: int, type_: str, payload: dict) -> None:
    db.add(core_models.ConversationEvent(conversation_id=conversation_id, type=type_, payload=payload))
    db.commit()


def _parse_price(text: str) -> tuple[float | None, float | None]:
    # aceita formatos simples: "2000-3500" ou "ate 3000" ou "3000"
    t = _normalize_text(text).replace("r$", "").replace(" ", "")
    if "-" in t:
        parts = t.split("-", 1)
        try:
            return float(parts[0]), float(parts[1])
        except Exception:
            return None, None
    if t.startswith("ate"):
        try:
            return None, float(t.replace("ate", ""))
        except Exception:
            return None, None
    try:
        v = float(t)
        return v, v
    except Exception:
        return None, None


def _process_realestate_funnel(db: Session, tenant_name: str, wa_id: str, user_text: str) -> str:
    """State machine mínima para coletar filtros de busca e retornar imóveis.

    Estados: purpose -> location_city -> location_state -> type -> bedrooms -> price -> done
    """
    tenant = _ensure_tenant(db, tenant_name)
    contact = _ensure_contact(db, tenant.id, wa_id)
    conv = _ensure_conversation(db, tenant.id, contact.id)

    text = _normalize_text(user_text)

    # Recuperar progresso anterior
    last = conv.last_state or "purpose"
    criteria: dict = {}
    # Buscar último event de tipo re_funnel se existir
    stmt = (
        select(core_models.ConversationEvent)
        .where(
            core_models.ConversationEvent.conversation_id == conv.id,
            core_models.ConversationEvent.type == "re_funnel",
        )
        .order_by(core_models.ConversationEvent.id.desc())
    )
    ev = db.execute(stmt).scalar_one_or_none()
    if ev and isinstance(ev.payload, dict):
        criteria = dict(ev.payload)

    def save_criteria(next_state: str) -> None:
        conv.last_state = next_state
        db.add(conv)
        _record_event(db, conv.id, "re_funnel", criteria)

    # State: purpose (compra/locação)
    if last == "purpose":
        if text in {"compra", "comprar", "venda", "buy", "sale"}:
            criteria["purpose"] = "sale"
            save_criteria("location_city")
            return "Legal! Você quer comprar. Me diga a cidade (ex: São Paulo)."
        if text in {"locacao", "locação", "aluguel", "alugar", "rent"}:
            criteria["purpose"] = "rent"
            save_criteria("location_city")
            return "Perfeito! Você quer alugar. Qual a cidade?"
        return "Olá! Você procura compra ou locação?"

    # State: cidade
    if last == "location_city":
        if len(text) < 2:
            return "Informe a cidade (ex: Campinas)."
        criteria["city"] = user_text.strip()
        save_criteria("location_state")
        return "Anotado. Qual o estado (UF)? (ex: SP)"

    # State: estado
    if last == "location_state":
        uf = text.upper().replace(" ", "")
        if len(uf) != 2:
            return "Informe a UF com 2 letras (ex: SP)."
        criteria["state"] = uf
        save_criteria("type")
        return "Certo. Prefere apartamento ou casa?"

    # State: tipo
    if last == "type":
        if text in {"ap", "apto", "apartamento", "apartment"}:
            criteria["type"] = "apartment"
        elif text in {"casa", "house"}:
            criteria["type"] = "house"
        else:
            return "Digite 'apartamento' ou 'casa'."
        save_criteria("bedrooms")
        return "Quantos dormitórios? (ex: 2)"

    # State: dormitórios
    if last == "bedrooms":
        try:
            n = int("".join(ch for ch in text if ch.isdigit()))
            criteria["bedrooms"] = n
            save_criteria("price")
            return "Qual a faixa de preço? (ex: 2000-3500 ou 'ate 3000')"
        except Exception:
            return "Informe um número de dormitórios (ex: 2)."

    # State: preço e busca
    if last == "price":
        min_p, max_p = _parse_price(user_text)
        if min_p is not None:
            criteria["min_price"] = min_p
        if max_p is not None:
            criteria["max_price"] = max_p

        # Criar lead e inquiry
        lead = re_models.Lead(
            tenant_id=tenant.id,
            name=None,
            phone=None,
            email=None,
            source="whatsapp",
            preferences=criteria,
            consent_lgpd=False,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        inquiry = re_models.Inquiry(
            tenant_id=tenant.id,
            lead_id=lead.id,
            property_id=None,
            type=re_models.InquiryType.buy if criteria.get("purpose") == "sale" else re_models.InquiryType.rent,
            status=re_models.InquiryStatus.new,
            payload=criteria,
        )
        db.add(inquiry)
        db.commit()

        # Buscar imóveis
        stmt = select(re_models.Property).where(re_models.Property.is_active == True)  # noqa: E712
        if criteria.get("purpose"):
            stmt = stmt.where(re_models.Property.purpose == re_models.PropertyPurpose(criteria["purpose"]))
        if criteria.get("type"):
            stmt = stmt.where(re_models.Property.type == re_models.PropertyType(criteria["type"]))
        if criteria.get("city"):
            stmt = stmt.where(re_models.Property.address_city.ilike(criteria["city"]))
        if criteria.get("state"):
            stmt = stmt.where(re_models.Property.address_state == criteria["state"])
        if criteria.get("bedrooms") is not None:
            stmt = stmt.where(re_models.Property.bedrooms >= int(criteria["bedrooms"]))
        if criteria.get("min_price") is not None:
            stmt = stmt.where(re_models.Property.price >= float(criteria["min_price"]))
        if criteria.get("max_price") is not None:
            stmt = stmt.where(re_models.Property.price <= float(criteria["max_price"]))

        stmt = stmt.limit(5)
        rows = db.execute(stmt).scalars().all()

        conv.last_state = "done"
        db.add(conv)
        db.commit()

        if not rows:
            return "Obrigado! Registrei sua preferência. No momento não encontrei imóveis com esse perfil. Quer ajustar a faixa de preço ou dormitórios?"

        lines = ["Encontrei estas opções:"]
        for p in rows:
            lines.append(f"#{p.id} - {p.title} | R$ {p.price:,.0f} | {p.address_city}-{p.address_state}")
        lines.append("Deseja ver mais detalhes? Envie o número do imóvel (ex: 3).")
        return "\n".join(lines)

    # State final ou desconhecido: reinicia
    conv.last_state = "purpose"
    db.add(conv)
    db.commit()
    return "Vamos começar! Você procura compra ou locação?"

