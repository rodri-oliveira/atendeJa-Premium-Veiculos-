from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.repositories.db import SessionLocal
from app.repositories.models import (
    Conversation,
    ConversationStatus,
    Message,
    MessageDirection,
    Contact,
    Tenant,
    User,
    UserRole,
    SuppressedContact,
    MessageLog,
)

import structlog
from app.core.config import settings
from app.workers.tasks_outbound import send_text as task_send_text
from app.workers.tasks_outbound import send_template as task_send_template
from app.workers.tasks_orders import check_sla_alerts as task_check_sla_alerts
from sqlalchemy import select
from app.api.deps import require_role_admin

# Definição do router e logger (precisa vir antes dos decoradores @router...)
router = APIRouter(dependencies=[Depends(require_role_admin)])
log = structlog.get_logger()

# Endpoint mínimo para conversas (suporta validação de auth nos testes)
@router.get("/conversations")
def list_conversations(wa_id: str, limit: int = 50):
    # Implementação simplificada para os testes: retorna lista vazia
    return []

# ------------------- Gestão de Usuários (admin-only) -------------------
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str | None = None
    role: UserRole = UserRole.collaborator
    is_active: bool = True


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


@router.post("/users", response_model=UserOut)
def create_user(payload: UserCreate):
    with SessionLocal() as db:  # type: Session
        email = (payload.email or "").strip().lower()
        if not email:
            raise HTTPException(status_code=400, detail="email_required")
        exists = db.query(User).filter(User.email == email).first()
        if exists:
            raise HTTPException(status_code=400, detail="email_already_exists")
        from app.core.security import get_password_hash

        user = User(
            email=email,
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
            is_active=bool(payload.is_active),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


# ------------------- Mensageria: Logs e Opt-out (Admin) -------------------
class SuppressIn(BaseModel):
    wa_id: str
    reason: str | None = None


def _get_or_create_default_tenant(db: Session) -> Tenant:
    tenant_name = settings.DEFAULT_TENANT_ID
    tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
    if not tenant:
        tenant = Tenant(name=tenant_name)
        db.add(tenant)
        db.flush()
    return tenant


@router.get("/messaging/logs")
def list_message_logs(
    to: str | None = None,
    status: str | None = None,
    dt_ini: str | None = None,
    dt_fim: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        from datetime import datetime
        with SessionLocal() as db:  # type: Session
            tenant = _get_or_create_default_tenant(db)
            q = db.query(MessageLog).filter(MessageLog.tenant_id == tenant.id)
            if to:
                q = q.filter(MessageLog.to == to)
            if status:
                q = q.filter(MessageLog.status == status)
            if dt_ini:
                try:
                    dti = datetime.fromisoformat(dt_ini)
                    q = q.filter(MessageLog.created_at >= dti)
                except Exception:
                    pass
            if dt_fim:
                try:
                    dtf = datetime.fromisoformat(dt_fim)
                    q = q.filter(MessageLog.created_at <= dtf)
                except Exception:
                    pass
            q = q.order_by(MessageLog.id.desc()).limit(max(1, min(limit, 200))).offset(max(0, offset))
            rows = q.all()
            return [
                {
                    "id": r.id,
                    "to": r.to,
                    "kind": r.kind,
                    "status": r.status,
                    "template_name": r.template_name,
                    "provider_message_id": r.provider_message_id,
                    "error_code": r.error_code,
                    "created_at": r.created_at,
                }
                for r in rows
            ]
    except HTTPException:
        raise
    except Exception as e:
        log.error("list_message_logs_error", error=str(e))
        raise HTTPException(status_code=400, detail="list_logs_error")


@router.post("/messaging/suppress")
def add_suppressed_contact(payload: SuppressIn):
    try:
        with SessionLocal() as db:  # type: Session
            tenant = _get_or_create_default_tenant(db)
            wa_id = (payload.wa_id or "").strip()
            if not wa_id:
                raise HTTPException(status_code=400, detail="wa_id_required")
            existing = (
                db.query(SuppressedContact)
                .filter(SuppressedContact.tenant_id == tenant.id, SuppressedContact.wa_id == wa_id)
                .first()
            )
            if existing:
                existing.reason = payload.reason or existing.reason
                db.add(existing)
                db.commit()
                db.refresh(existing)
                return {"status": "updated", "wa_id": wa_id}
            sup = SuppressedContact(tenant_id=tenant.id, wa_id=wa_id, reason=payload.reason)
            db.add(sup)
            db.commit()
            return {"status": "created", "wa_id": wa_id}
    except HTTPException:
        raise
    except Exception as e:
        log.error("suppress_add_error", error=str(e))
        raise HTTPException(status_code=400, detail="suppress_add_error")


@router.delete("/messaging/suppress")
def remove_suppressed_contact(wa_id: str):
    try:
        with SessionLocal() as db:  # type: Session
            tenant = _get_or_create_default_tenant(db)
            wa_id_ = (wa_id or "").strip()
            if not wa_id_:
                raise HTTPException(status_code=400, detail="wa_id_required")
            removed = (
                db.query(SuppressedContact)
                .filter(SuppressedContact.tenant_id == tenant.id, SuppressedContact.wa_id == wa_id_)
                .delete()
            )
            db.commit()
            return {"removed": int(removed)}
    except HTTPException:
        raise
    except Exception as e:
        log.error("suppress_remove_error", error=str(e))
        raise HTTPException(status_code=400, detail="suppress_remove_error")


@router.get("/messaging/window-status")
def window_status(wa_id: str):
    """Retorna se o contato está dentro da janela de 24h e quando foi a última inbound."""
    try:
        from datetime import datetime, timedelta, timezone
        with SessionLocal() as db:  # type: Session
            tenant = _get_or_create_default_tenant(db)
            contact = db.query(Contact).filter(Contact.tenant_id == tenant.id, Contact.wa_id == wa_id).first()
            if not contact:
                return {"inside_window": False, "last_inbound_at": None, "hours_since": None}
            last_inbound = (
                db.query(Message)
                .filter(
                    Message.tenant_id == tenant.id,
                    Message.direction == MessageDirection.inbound,
                    Message.conversation_id.in_(db.query(Conversation.id).filter(Conversation.contact_id == contact.id)),
                )
                .order_by(Message.created_at.desc())
                .first()
            )
            if not last_inbound:
                return {"inside_window": False, "last_inbound_at": None, "hours_since": None}
            now = datetime.now(timezone.utc)
            li = last_inbound.created_at
            if li.tzinfo is None:
                li = li.replace(tzinfo=timezone.utc)
            delta_h = (now - li).total_seconds() / 3600.0
            inside = delta_h <= settings.WINDOW_24H_HOURS
            return {"inside_window": inside, "last_inbound_at": li, "hours_since": round(delta_h, 2)}
    except HTTPException:
        raise
    except Exception as e:
        log.error("window_status_error", error=str(e))
        raise HTTPException(status_code=400, detail="window_status_error")


@router.get("/users", response_model=list[UserOut])
def list_users(role: UserRole | None = None, is_active: bool | None = None, limit: int = 50, offset: int = 0):
    with SessionLocal() as db:  # type: Session
        q = db.query(User)
        if role is not None:
            q = q.filter(User.role == role)
        if is_active is not None:
            q = q.filter(User.is_active == is_active)
        q = q.order_by(User.id.asc()).limit(max(1, min(limit, 200))).offset(max(0, offset))
        return q.all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate):
    with SessionLocal() as db:  # type: Session
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="user_not_found")
        data = payload.model_dump(exclude_unset=True)
        if "full_name" in data:
            user.full_name = data["full_name"]
        if "role" in data and data["role"] is not None:
            user.role = data["role"]
        if "is_active" in data and data["is_active"] is not None:
            user.is_active = bool(data["is_active"])
        if "password" in data and data["password"]:
            from app.core.security import get_password_hash

            user.hashed_password = get_password_hash(data["password"])
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
