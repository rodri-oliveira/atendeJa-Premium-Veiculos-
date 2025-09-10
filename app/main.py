from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import configure_logging
from app.api.routes.health import router as health_router
from app.api.routes.webhook import router as webhook_router
from app.api.routes.admin import router as admin_router
from app.repositories.db import engine
from app.repositories.models import Base

configure_logging()

app = FastAPI(title="AtendeJá Chatbot API", version="0.1.0")

app.include_router(health_router, prefix="/health", tags=["health"]) 
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"]) 
app.include_router(admin_router, prefix="/admin", tags=["admin"]) 

@app.get("/")
async def root():
    return {"service": "atendeja-chatbot", "status": "ok"}


@app.on_event("startup")
def on_startup() -> None:
    # Dev convenience: create tables if they don't exist. In prod, use Alembic migrations.
    Base.metadata.create_all(bind=engine)
