from celery import Celery
from app.core.config import settings

celery = Celery(
    "atendeja",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks_inbound",
        "app.workers.tasks_outbound",
    ],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery.task(name="echo")
def echo(message: str) -> str:
    return f"echo: {message}"

# Ensure tasks modules are imported for registration when running in some environments
try:  # pragma: no cover
    import app.workers.tasks_inbound  # noqa: F401
    import app.workers.tasks_outbound  # noqa: F401
except Exception:  # noqa: BLE001
    pass
