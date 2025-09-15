from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.repositories.db import SessionLocal
from app.repositories.models import Conversation, ConversationStatus, Message, Contact, Tenant
import structlog
from app.core.config import settings
from app.workers.tasks_outbound import send_text as task_send_text
from app.workers.tasks_outbound import send_template as task_send_template
from app.workers.tasks_orders import check_sla_alerts as task_check_sla_alerts
from sqlalchemy import select, delete
from app.domain.realestate import models as re_models
import csv
import io

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


# ------------------- Importação CSV de imóveis (MVP) -------------------
CSV_COLUMNS = [
    "titulo","descricao","tipo","finalidade","preco","condominio","iptu",
    "cidade","estado","bairro","dormitorios","banheiros","suites","vagas",
    "area_total","area_util","ano_construcao","external_id","source","updated_at_source","imagens_urls"
]


def _to_float(v: str | None) -> float | None:
    if v is None:
        return None
    s = str(v).strip().replace("R$", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def _to_int(v: str | None) -> int | None:
    if v is None:
        return None
    try:
        return int(str(v).strip())
    except Exception:
        return None


@router.post("/re/imoveis/import-csv", summary="Importa imóveis via CSV (upsert por external_id)")
def import_imoveis_csv(file: UploadFile = File(...)):
    try:
        if settings.RE_READ_ONLY:
            raise HTTPException(status_code=403, detail="read_only_mode")

        # Log de entrada
        log.info("csv_import_request", filename=getattr(file, "filename", None), content_type=getattr(file, "content_type", None))

        content = file.file.read()
        # Tamanho do arquivo
        log.info("csv_import_size", bytes=len(content))

        try:
            text = content.decode("utf-8")
        except Exception:
            text = content.decode("latin-1")
        # Remove BOM se presente (PowerShell UTF8 com BOM)
        if text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")

        sio = io.StringIO(text)
        reader = csv.DictReader(sio)
        # Normaliza headers lidos: strip/lower/BOM-safe
        read_headers = {h.strip().lower().lstrip("\ufeff") for h in (reader.fieldnames or [])}
        try:
            preview_row = next(iter(list(csv.reader(io.StringIO(text)))))
        except Exception:
            preview_row = []
        log.info("csv_import_headers", headers=sorted(list(read_headers)), preview_first_row=preview_row)
        missing_cols = [c for c in CSV_COLUMNS if c not in read_headers]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "missing_columns",
                    "message": "Colunas ausentes no CSV",
                    "columns": missing_cols,
                    "received": sorted(list(read_headers)),
                },
            )

        created = 0
        updated = 0
        images_created = 0
        tenant_name = settings.DEFAULT_TENANT_ID

        with SessionLocal() as db:  # type: Session
            tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
            if not tenant:
                tenant = Tenant(name=tenant_name)
                db.add(tenant)
                db.flush()

            for row in reader:
                ext_id = (row.get("external_id") or "").strip()
                source = (row.get("source") or "").strip() or None
                if not ext_id:
                    # p/ simplicidade, ignoramos linhas sem external_id
                    log.warn("csv_row_skipped_no_external_id", row=row)
                    continue

                # busca existente
                stmt = select(re_models.Property).where(
                    re_models.Property.tenant_id == tenant.id,
                    re_models.Property.external_id == ext_id,
                )
                prop = db.execute(stmt).scalar_one_or_none()

                # converte campos
                tipo = (row.get("tipo") or "").strip().lower()
                finalidade = (row.get("finalidade") or "").strip().lower()
                try:
                    type_enum = re_models.PropertyType(tipo)
                except Exception:
                    type_enum = re_models.PropertyType.apartment if "ap" in tipo else re_models.PropertyType.house
                try:
                    purpose_enum = re_models.PropertyPurpose(finalidade)
                except Exception:
                    purpose_enum = re_models.PropertyPurpose.rent if "alug" in finalidade or "rent" in finalidade else re_models.PropertyPurpose.sale

                preco = _to_float(row.get("preco")) or 0.0
                condominio = _to_float(row.get("condominio"))
                iptu = _to_float(row.get("iptu"))

                bedrooms = _to_int(row.get("dormitorios"))
                bathrooms = _to_int(row.get("banheiros"))
                suites = _to_int(row.get("suites"))
                vagas = _to_int(row.get("vagas"))
                area_total = _to_float(row.get("area_total"))
                area_util = _to_float(row.get("area_util"))

                img_urls = [u.strip() for u in (row.get("imagens_urls") or "").split(";") if u.strip()]

                # parse updated_at_source (ISO) simples
                updated_at_source = (row.get("updated_at_source") or "").strip() or None

                if prop is None:
                    prop = re_models.Property(
                        tenant_id=tenant.id,
                        title=(row.get("titulo") or "").strip() or "Sem título",
                        description=(row.get("descricao") or None),
                        type=type_enum,
                        purpose=purpose_enum,
                        price=preco,
                        condo_fee=condominio,
                        iptu=iptu,
                        external_id=ext_id,
                        source=source,
                        updated_at_source=updated_at_source,
                        address_city=(row.get("cidade") or "").strip(),
                        address_state=(row.get("estado") or "").strip().upper(),
                        address_neighborhood=(row.get("bairro") or None),
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        suites=suites,
                        parking_spots=vagas,
                        area_total=area_total,
                        area_usable=area_util,
                        is_active=True,
                    )
                    db.add(prop)
                    db.flush()
                    created += 1
                else:
                    # update campos básicos
                    prop.title = (row.get("titulo") or prop.title)
                    prop.description = (row.get("descricao") or prop.description)
                    prop.type = type_enum
                    prop.purpose = purpose_enum
                    prop.price = preco or prop.price
                    prop.condo_fee = condominio
                    prop.iptu = iptu
                    prop.source = source
                    prop.updated_at_source = updated_at_source
                    prop.address_city = (row.get("cidade") or prop.address_city)
                    prop.address_state = (row.get("estado") or prop.address_state)
                    prop.address_neighborhood = (row.get("bairro") or prop.address_neighborhood)
                    prop.bedrooms = bedrooms
                    prop.bathrooms = bathrooms
                    prop.suites = suites
                    prop.parking_spots = vagas
                    prop.area_total = area_total
                    prop.area_usable = area_util
                    updated += 1

                # imagens: remove antigas e insere novas se fornecidas
                if img_urls:
                    db.execute(delete(re_models.PropertyImage).where(re_models.PropertyImage.property_id == prop.id))
                    ord_ = 0
                    for idx, url in enumerate(img_urls):
                        img = re_models.PropertyImage(
                            property_id=prop.id,
                            url=url,
                            is_cover=(idx == 0),
                            sort_order=ord_,
                        )
                        db.add(img)
                        ord_ += 1
                        images_created += 1

            db.commit()

        return {"created": created, "updated": updated, "images_created": images_created}
    except HTTPException:
        # repassa HTTPException para os handlers
        raise
    except Exception as e:
        log.error("csv_import_error", error=str(e))
        raise HTTPException(status_code=400, detail={"code": "csv_parse_error", "message": str(e)})


@router.post("/re/imoveis/import-csv-raw", summary="Importa imóveis via CSV bruto no corpo (text/csv)")
async def import_imoveis_csv_raw(request: Request):
    try:
        if settings.RE_READ_ONLY:
            raise HTTPException(status_code=403, detail="read_only_mode")

        body = await request.body()
        log.info("csv_import_raw_size", bytes=len(body))
        try:
            text = body.decode("utf-8")
        except Exception:
            text = body.decode("latin-1")
        if text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")

        sio = io.StringIO(text)
        reader = csv.DictReader(sio)
        read_headers = {h.strip().lower().lstrip("\ufeff") for h in (reader.fieldnames or [])}
        try:
            preview_row = next(iter(list(csv.reader(io.StringIO(text)))))
        except Exception:
            preview_row = []
        log.info("csv_import_raw_headers", headers=sorted(list(read_headers)), preview_first_row=preview_row)
        missing_cols = [c for c in CSV_COLUMNS if c not in read_headers]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "missing_columns",
                    "message": "Colunas ausentes no CSV",
                    "columns": missing_cols,
                    "received": sorted(list(read_headers)),
                },
            )

        created = 0
        updated = 0
        images_created = 0
        tenant_name = settings.DEFAULT_TENANT_ID
        with SessionLocal() as db:  # type: Session
            tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
            if not tenant:
                tenant = Tenant(name=tenant_name)
                db.add(tenant)
                db.flush()

            for row in reader:
                ext_id = (row.get("external_id") or "").strip()
                source = (row.get("source") or "").strip() or None
                if not ext_id:
                    log.warn("csv_row_skipped_no_external_id", row=row)
                    continue
                stmt = select(re_models.Property).where(
                    re_models.Property.tenant_id == tenant.id,
                    re_models.Property.external_id == ext_id,
                )
                prop = db.execute(stmt).scalar_one_or_none()

                tipo = (row.get("tipo") or "").strip().lower()
                finalidade = (row.get("finalidade") or "").strip().lower()
                try:
                    type_enum = re_models.PropertyType(tipo)
                except Exception:
                    type_enum = re_models.PropertyType.apartment if "ap" in tipo else re_models.PropertyType.house
                try:
                    purpose_enum = re_models.PropertyPurpose(finalidade)
                except Exception:
                    purpose_enum = re_models.PropertyPurpose.rent if "alug" in finalidade or "rent" in finalidade else re_models.PropertyPurpose.sale

                preco = _to_float(row.get("preco")) or 0.0
                condominio = _to_float(row.get("condominio"))
                iptu = _to_float(row.get("iptu"))
                bedrooms = _to_int(row.get("dormitorios"))
                bathrooms = _to_int(row.get("banheiros"))
                suites = _to_int(row.get("suites"))
                vagas = _to_int(row.get("vagas"))
                area_total = _to_float(row.get("area_total"))
                area_util = _to_float(row.get("area_util"))
                img_urls = [u.strip() for u in (row.get("imagens_urls") or "").split(";") if u.strip()]
                updated_at_source = (row.get("updated_at_source") or "").strip() or None

                if prop is None:
                    prop = re_models.Property(
                        tenant_id=tenant.id,
                        title=(row.get("titulo") or "").strip() or "Sem título",
                        description=(row.get("descricao") or None),
                        type=type_enum,
                        purpose=purpose_enum,
                        price=preco,
                        condo_fee=condominio,
                        iptu=iptu,
                        external_id=ext_id,
                        source=source,
                        updated_at_source=updated_at_source,
                        address_city=(row.get("cidade") or "").strip(),
                        address_state=(row.get("estado") or "").strip().upper(),
                        address_neighborhood=(row.get("bairro") or None),
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        suites=suites,
                        parking_spots=vagas,
                        area_total=area_total,
                        area_usable=area_util,
                        is_active=True,
                    )
                    db.add(prop)
                    db.flush()
                    created += 1
                else:
                    prop.title = (row.get("titulo") or prop.title)
                    prop.description = (row.get("descricao") or prop.description)
                    prop.type = type_enum
                    prop.purpose = purpose_enum
                    prop.price = preco or prop.price
                    prop.condo_fee = condominio
                    prop.iptu = iptu
                    prop.source = source
                    prop.updated_at_source = updated_at_source
                    prop.address_city = (row.get("cidade") or prop.address_city)
                    prop.address_state = (row.get("estado") or prop.address_state)
                    prop.address_neighborhood = (row.get("bairro") or prop.address_neighborhood)
                    prop.bedrooms = bedrooms
                    prop.bathrooms = bathrooms
                    prop.suites = suites
                    prop.parking_spots = vagas
                    prop.area_total = area_total
                    prop.area_usable = area_util
                    updated += 1

                if img_urls:
                    db.execute(delete(re_models.PropertyImage).where(re_models.PropertyImage.property_id == prop.id))
                    ord_ = 0
                    for idx, url in enumerate(img_urls):
                        img = re_models.PropertyImage(
                            property_id=prop.id,
                            url=url,
                            is_cover=(idx == 0),
                            sort_order=ord_,
                        )
                        db.add(img)
                        ord_ += 1
                        images_created += 1

            db.commit()

        return {"created": created, "updated": updated, "images_created": images_created}
    except HTTPException:
        raise
    except Exception as e:
        log.error("csv_import_raw_error", error=str(e))
        raise HTTPException(status_code=400, detail={"code": "csv_parse_error", "message": str(e)})
