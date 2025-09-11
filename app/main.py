from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.api.errors import http_exception_handler, validation_exception_handler, generic_exception_handler
from app.core.config import settings
from app.core.logging import configure_logging
from app.api.routes.health import router as health_router
from app.api.routes.webhook import router as webhook_router
from app.api.routes.admin import router as admin_router
from app.api.routes.menu import router as menu_router
from app.api.routes.orders import router as orders_router
from app.repositories.db import engine
from app.repositories.models import Base
from contextlib import asynccontextmanager

configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.APP_ENV != "test":  # skip for tests to speed up
        Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: nothing for now


app = FastAPI(title="AtendeJá Chatbot API", version="0.1.0", lifespan=lifespan)

app.include_router(health_router, prefix="/health", tags=["health"]) 
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"]) 
app.include_router(admin_router, prefix="/admin", tags=["admin"]) 
app.include_router(menu_router, prefix="/menu", tags=["menu"]) 
app.include_router(orders_router, prefix="/orders", tags=["orders"]) 

# Global error handlers (uniform error payloads)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

@app.get("/")
async def root():
    return {"service": "atendeja-chatbot", "status": "ok"}
