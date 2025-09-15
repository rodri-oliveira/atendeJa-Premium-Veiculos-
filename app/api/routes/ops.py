from __future__ import annotations
from fastapi import APIRouter
import httpx
from app.core.config import settings

router = APIRouter()


@router.get("/ping/meta", summary="Healthcheck do provider Meta Cloud (sem custo)")
async def ping_meta():
    # Valida variáveis essenciais
    problems: list[str] = []
    if not settings.WA_TOKEN:
        problems.append("WA_TOKEN ausente")
    if not settings.WA_PHONE_NUMBER_ID:
        problems.append("WA_PHONE_NUMBER_ID ausente")
    if not settings.WA_API_BASE:
        problems.append("WA_API_BASE ausente")

    checks: dict = {"env_ok": len(problems) == 0, "problems": problems}

    # Checagem leve de rede (HEAD na Graph API) – não gera custo
    try:
        url = settings.WA_API_BASE.rstrip("/")
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.head(url)
        checks["graph_head_status"] = r.status_code
        checks["graph_reachable"] = r.status_code < 500
    except Exception as e:  # noqa: BLE001
        checks["graph_reachable"] = False
        checks["error"] = str(e)

    return checks


@router.get("/config", summary="Configurações não sensíveis (observabilidade leve)")
async def config_info():
    try:
        wa_provider = getattr(settings, "WA_PROVIDER", None) or "meta"
    except Exception:
        wa_provider = "meta"
    return {
        "app_env": settings.APP_ENV,
        "wa_provider": wa_provider,
        "default_tenant": settings.DEFAULT_TENANT_ID,
        "re_read_only": bool(getattr(settings, "RE_READ_ONLY", False)),
        "version": "0.1.0",
    }
