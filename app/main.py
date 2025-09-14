from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.api.errors import http_exception_handler, validation_exception_handler, generic_exception_handler
from app.core.config import settings
from app.core.logging import configure_logging
from app.api.routes.health import router as health_router
from app.api.routes.webhook import router as webhook_router
from app.api.routes.admin import router as admin_router
from app.api.routes.realestate import router as realestate_router
from app.api.routes.mcp import router as mcp_router
from app.repositories.db import engine
from app.repositories.models import Base
import app.domain.realestate.models  # noqa: F401 - importa modelos para registrar no metadata
from contextlib import asynccontextmanager

configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.APP_ENV != "test":  # skip for tests to speed up
        Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: nothing for now


tags_metadata = [
    {"name": "health", "description": "Healthchecks de liveness/readiness."},
    {"name": "webhook", "description": "Webhook do WhatsApp Cloud API."},
    {"name": "admin", "description": "Endpoints administrativos (futuros)."},
    {"name": "realestate", "description": "Domínio imobiliário: imóveis e leads."},
]

app = FastAPI(
    title="AtendeJá Chatbot API",
    version="0.1.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/health", tags=["health"]) 
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"]) 
app.include_router(admin_router, prefix="/admin", tags=["admin"]) 
app.include_router(realestate_router, prefix="/re", tags=["realestate"]) 
app.include_router(mcp_router, prefix="/mcp", tags=["mcp"]) 

# Global error handlers (uniform error payloads)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

@app.get("/")
async def root():
    return {"service": "atendeja-chatbot", "status": "ok"}
