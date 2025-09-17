from __future__ import annotations
from fastapi import APIRouter
import httpx
from app.core.config import settings
from fastapi import HTTPException, Query
from app.integrations.pan import PanService

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


@router.get("/pan/check", summary="Valida variáveis de ambiente do Banco Pan (sem expor segredos)")
async def pan_env_check():
    missing: list[str] = []
    def _has(v: str) -> bool:
        return bool((v or "").strip())

    base_url_ok = _has(settings.PAN_BASE_URL)
    api_key_ok = _has(settings.PAN_API_KEY)
    basic_ok = ":" in ((settings.PAN_BASIC_CREDENTIALS or "").strip())
    user_ok = _has(settings.PAN_USERNAME)
    pass_ok = _has(settings.PAN_PASSWORD)
    loja_ok = _has(settings.PAN_LOJA_ID)

    if not base_url_ok:
        missing.append("PAN_BASE_URL")
    if not api_key_ok:
        missing.append("PAN_API_KEY")
    if not basic_ok:
        missing.append("PAN_BASIC_CREDENTIALS (formato APIKEY:SECRETKEY)")
    if not user_ok:
        missing.append("PAN_USERNAME")
    if not pass_ok:
        missing.append("PAN_PASSWORD")
    if not loja_ok:
        missing.append("PAN_LOJA_ID")

    return {
        "ok": len(missing) == 0,
        "missing": missing,
        "base_url_set": base_url_ok,
        "api_key_set": api_key_ok,
        "basic_pair_set": basic_ok,
        "username_set": user_ok,
        "password_set": pass_ok,
        "loja_set": loja_ok,
    }


@router.get("/pan/token", summary="Obtém token do Pan (respeita PAN_MOCK)")
async def pan_token():
    try:
        svc = PanService()
        token = svc.obter_token(force_refresh=True)
        return {"ok": True, "token_preview": (token[:8] + "..." if token else ""), "mock": bool(getattr(settings, "PAN_MOCK", False))}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pan/preanalise", summary="Chama pré-análise do Pan (respeita PAN_MOCK)")
async def pan_preanalise(cpf: str = Query(...), categoria: str | None = Query(default=None)):
    try:
        svc = PanService()
        res = svc.pre_analise(cpf=cpf, categoria=categoria)
        return res
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(e))
