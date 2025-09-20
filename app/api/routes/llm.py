from fastapi import APIRouter, HTTPException
import httpx
from app.core.config import settings

router = APIRouter()

OLLAMA_URL = (settings.OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")

def _candidate_urls() -> list[str]:
    base = OLLAMA_URL
    urls = [base]
    # fallback comuns para Docker Desktop no Windows
    if "host.docker.internal" not in base:
        urls.append("http://host.docker.internal:11434")
    if "localhost" not in base and "127.0.0.1" not in base:
        urls.append("http://localhost:11434")
    # remover duplicados mantendo ordem
    dedup: list[str] = []
    for u in urls:
        u = u.rstrip("/")
        if u not in dedup:
            dedup.append(u)
    return dedup

@router.get("/llm/ping")
async def llm_ping():
    attempts = []
    async with httpx.AsyncClient(timeout=5) as client:
        for base in _candidate_urls():
            try:
                r = await client.get(f"{base}/api/tags")
                attempts.append({"url": base, "status": r.status_code})
                if r.status_code == 200:
                    return {"ok": True, "used_url": base, "attempts": attempts}
            except Exception as e:  # noqa: BLE001
                attempts.append({"url": base, "error": str(e)})
                continue
    return {"ok": False, "attempts": attempts}

@router.post("/llm/generate")
async def llm_generate(payload: dict):
    """Proxy simples para o Ollama /api/generate com stream desativado por padrão.
    payload aceito: { prompt: str, model?: str, temperature?: float, stream?: bool }
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid_payload")
    model = payload.get("model") or "gemma3:1b"
    prompt = payload.get("prompt") or ""
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt_required")
    options = {}
    if "temperature" in payload:
        options["temperature"] = payload.get("temperature")
    body = {"model": model, "prompt": prompt, "stream": bool(payload.get("stream", False))}
    if options:
        body["options"] = options
    last_err: str | None = None
    async with httpx.AsyncClient(timeout=60) as client:
        for base in _candidate_urls():
            try:
                r = await client.post(f"{base}/api/generate", json=body)
                if r.status_code == 200:
                    data = r.json()
                    return {"model": model, "response": data.get("response", ""), "raw": data, "used_url": base}
                last_err = f"HTTP {r.status_code}: {r.text}"
            except Exception as e:  # noqa: BLE001
                last_err = str(e)
                continue
    raise HTTPException(status_code=502, detail=f"ollama_unreachable: {last_err}")


@router.post("/llm/chat")
async def llm_chat(payload: dict):
    """Proxy simples para o Ollama /api/chat (sem stream por padrão).
    payload aceito: { messages: [{role, content}], model?: str, stream?: bool }
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid_payload")
    model = payload.get("model") or "gemma3:1b"
    messages = payload.get("messages") or []
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="messages_required")
    body = {"model": model, "messages": messages, "stream": bool(payload.get("stream", False))}
    last_err: str | None = None
    async with httpx.AsyncClient(timeout=60) as client:
        for base in _candidate_urls():
            try:
                r = await client.post(f"{base}/api/chat", json=body)
                if r.status_code == 200:
                    data = r.json()
                    data["used_url"] = base
                    return data
                last_err = f"HTTP {r.status_code}: {r.text}"
            except Exception as e:  # noqa: BLE001
                last_err = str(e)
                continue
    raise HTTPException(status_code=502, detail=f"ollama_unreachable: {last_err}")
