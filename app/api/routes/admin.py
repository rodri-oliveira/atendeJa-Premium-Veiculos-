from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.repositories.db import SessionLocal
from app.repositories.models import (
    Conversation,
    ConversationStatus,
    Message,
    Contact,
    Tenant,
    User,
    UserRole,
)

import structlog
from app.core.config import settings
from app.workers.tasks_outbound import send_text as task_send_text
from app.workers.tasks_outbound import send_template as task_send_template
from app.workers.tasks_orders import check_sla_alerts as task_check_sla_alerts
from sqlalchemy import select, delete
from app.domain.realestate import models as re_models
import csv
import io
from app.api.deps import require_role_admin

# Definição do router e logger (precisa vir antes dos decoradores @router...)
router = APIRouter(dependencies=[Depends(require_role_admin)])
log = structlog.get_logger()

# Endpoint mínimo para conversas (suporta validação de auth nos testes)
@router.get("/conversations")
def list_conversations(wa_id: str, limit: int = 50):
    # Implementação simplificada para os testes: retorna lista vazia
    return []

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


def _to_dt(v: str | None):
    """Converte string ISO-8601 simples para datetime; aceita sufixo 'Z'."""
    if not v:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        from datetime import datetime
        return datetime.fromisoformat(s)
    except Exception:
        return None


@router.post("/re/imoveis/import-csv", summary="Importa imóveis via CSV (upsert por external_id)")
def import_imoveis_csv(file: UploadFile = File(...)):
    try:
        if settings.RE_READ_ONLY:
            raise HTTPException(status_code=403, detail="read_only_mode")

        log.info("csv_import_request", filename=getattr(file, "filename", None), content_type=getattr(file, "content_type", None))
        content = file.file.read()
        log.info("csv_import_size", bytes=len(content))

        try:
            text = content.decode("utf-8")
        except Exception:
            text = content.decode("latin-1")
        if text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")

        sio = io.StringIO(text)
        reader = csv.DictReader(sio)
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

                updated_at_source = _to_dt(row.get("updated_at_source"))

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
        log.error("csv_import_error", error=str(e))
        raise HTTPException(status_code=400, detail={"code": "csv_parse_error", "message": str(e)})

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
