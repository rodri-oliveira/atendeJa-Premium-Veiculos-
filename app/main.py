from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.api.errors import http_exception_handler, validation_exception_handler, generic_exception_handler
from app.core.config import settings
from app.core.logging import configure_logging
from app.api.routes.health import router as health_router
from app.api.routes.ops import router as ops_router
from app.api.routes.webhook import router as webhook_router
from app.api.routes.vehicles import router as vehicles_router
from app.api.routes.admin import router as admin_router
from app.api.routes.mcp import router as mcp_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.auth import router as auth_router
from app.repositories.db import engine
from app.repositories.models import Base, User, UserRole
from contextlib import asynccontextmanager
import structlog
import traceback
from fastapi.responses import JSONResponse
import structlog
import traceback
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.repositories.db import SessionLocal
from app.core.security import get_password_hash

configure_logging()
log = structlog.get_logger()
log = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.APP_ENV != "test":  # skip for tests to speed up
        Base.metadata.create_all(bind=engine)
        # Seed do usuário admin, se configurado
        try:
            seed_email = (settings.AUTH_SEED_ADMIN_EMAIL or "").strip().lower()
            seed_password = (settings.AUTH_SEED_ADMIN_PASSWORD or "").strip()
            if seed_email and seed_password:
                with SessionLocal() as db:  # type: Session
                    user = db.query(User).filter(User.email == seed_email).first()
                    if not user:
                        user = User(
                            email=seed_email,
                            full_name="Admin",
                            hashed_password=get_password_hash(seed_password),
                            is_active=True,
                            role=UserRole.admin,
                        )
                        db.add(user)
                        db.commit()
                        log.info("admin_seeded", email=seed_email)
        except Exception as e:
            log.error("admin_seed_error", error=str(e))
    yield
    # Shutdown: nothing for now


tags_metadata = [
    {"name": "health", "description": "Healthchecks de liveness/readiness."},
    {"name": "webhook", "description": "Webhook do WhatsApp Cloud API."},
    {"name": "ops", "description": "Operações e healthchecks de integrações."},
    {"name": "admin", "description": "Endpoints administrativos (futuros)."},
    {"name": "auth", "description": "Autenticação JWT e informações do usuário."},
    {"name": "vehicles", "description": "Catálogo de veículos (POC)."},
]

# Adiciona tag do domínio imobiliário apenas se habilitado
if settings.REAL_ESTATE_ENABLED:
    tags_metadata.append({"name": "realestate", "description": "Domínio imobiliário: imóveis e leads."})

app = FastAPI(
    title="AtendeJá Chatbot API",
    version="0.1.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

@app.middleware("http")
async def _http_logger(request, call_next):
    try:
        try:
            body_bytes = await request.body()
        except Exception:
            body_bytes = b""
        log.info(
            "http_request_start",
            method=request.method,
            path=request.url.path,
            content_type=request.headers.get("content-type"),
            content_length=len(body_bytes) if body_bytes is not None else 0,
        )
        response = await call_next(request)
        log.info(
            "http_request_end",
            method=request.method,
            path=request.url.path,
            status=getattr(response, "status_code", None),
        )
        return response
    except Exception as e:
        log.error(
            "http_request_exception",
            method=request.method,
            path=request.url.path,
            error=str(e),
            traceback=traceback.format_exc(),
        )
        return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "unexpected error"}})

app.include_router(health_router, prefix="/health", tags=["health"]) 
app.include_router(ops_router, prefix="/ops", tags=["ops"]) 
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"]) 
app.include_router(admin_router, prefix="/admin", tags=["admin"]) 
app.include_router(mcp_router, prefix="/mcp", tags=["mcp"]) 
app.include_router(auth_router, prefix="/auth", tags=["auth"]) 
app.include_router(metrics_router, prefix="/metrics", tags=["metrics"]) 
app.include_router(vehicles_router, tags=["vehicles"]) 

# Inclui rotas e modelos do domínio imobiliário somente quando habilitado
if settings.REAL_ESTATE_ENABLED:
    # Importação tardia para evitar carregamento quando desabilitado
    import app.domain.realestate.models  # noqa: F401 - registra modelos no metadata
    from app.api.routes.realestate import router as realestate_router
    app.include_router(realestate_router, prefix="/re", tags=["realestate"]) 

# Global error handlers (uniform error payloads)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

@app.get("/")
async def root():
    return {"service": "atendeja-chatbot", "status": "ok"}
