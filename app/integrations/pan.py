import base64
import time
from typing import Any, Dict, Optional

import httpx
import structlog

from app.core.config import settings

log = structlog.get_logger()


class _TokenCache:
    def __init__(self) -> None:
        self.value: Optional[str] = None
        self.expires_at: float = 0.0

    def set(self, token: str, ttl_seconds: int) -> None:
        # margem de segurança de 60s
        self.value = token
        self.expires_at = time.time() + max(ttl_seconds - 60, 60)

    def get(self) -> Optional[str]:
        if not self.value:
            return None
        if time.time() >= self.expires_at:
            return None
        return self.value


token_cache = _TokenCache()


def _basic_auth_header(creds_pair: str) -> str:
    enc = base64.b64encode(creds_pair.encode("utf-8")).decode("ascii")
    return f"Basic {enc}"


def mask_cpf(cpf: str) -> str:
    digits = ''.join([c for c in cpf if c.isdigit()])
    if len(digits) < 4:
        return "***"
    return "***" + digits[-5:-2] + "-" + digits[-2:]


class PanService:
    def __init__(self) -> None:
        self.mock = bool(getattr(settings, "PAN_MOCK", False))
        self.base_url = (settings.PAN_BASE_URL or "").rstrip("/")
        self.api_key = settings.PAN_API_KEY or ""
        self.basic_pair = (settings.PAN_BASIC_CREDENTIALS or "").strip()
        self.username = settings.PAN_USERNAME or ""
        self.password = settings.PAN_PASSWORD or ""
        self.default_loja = settings.PAN_LOJA_ID or ""
        if self.mock:
            # No modo mock, não exigimos credenciais/URLs
            log.info("pan_mock_enabled")
            return
        if not self.base_url:
            raise ValueError("PAN_BASE_URL não configurado")
        if not self.api_key:
            raise ValueError("PAN_API_KEY não configurado")
        if not self.basic_pair or ":" not in self.basic_pair:
            raise ValueError("PAN_BASIC_CREDENTIALS ausente ou inválido (use APIKEY:SECRETKEY)")
        if not self.username or not self.password:
            raise ValueError("PAN_USERNAME/PAN_PASSWORD não configurados")

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=8.0)

    def obter_token(self, force_refresh: bool = False) -> str:
        if self.mock:
            # Token simulado com cache simples
            cached = token_cache.get()
            if cached and not force_refresh:
                return cached
            token = "mock-token-pan"
            token_cache.set(token, 1800)
            log.info("pan_token_ok", ttl=1800, mock=True)
            return token
        cached = token_cache.get()
        if cached and not force_refresh:
            return cached

        url = f"{self.base_url}/veiculos/v0/tokens"
        headers = {
            "Content-Type": "application/json",
            "ApiKey": self.api_key,
            "Authorization": _basic_auth_header(self.basic_pair),
        }
        payload = {
            "username": self.username,
            "password": self.password,
            "grant_type": "client_credentials+password",
        }
        with self._client() as client:
            resp = client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            log.error("pan_token_error", status=resp.status_code, body=resp.text[:500])
            resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token") or data.get("token") or ""
        expires_in = int(data.get("expires_in", 1800))
        if not token:
            raise RuntimeError("Resposta do PAN não contém token")
        token_cache.set(token, expires_in)
        log.info("pan_token_ok", ttl=expires_in)
        return token

    def pre_analise(self, cpf: str, categoria: Optional[str] = None, id_loja: Optional[str] = None) -> Dict[str, Any]:
        # A doc do PAN exige categoriaVeiculo como LEVES|MOTOS. Mapeamos entradas comuns para esses valores.
        raw = (categoria or settings.PAN_DEFAULT_CATEGORIA or "USADO").upper()
        if any(k in raw for k in ["MOTO", "MOTOS"]):
            cat = "MOTOS"
        else:
            # Para NOVO/USADO, assumimos categoria veicular LEVES
            cat = "LEVES"
        loja = id_loja or self.default_loja or ""
        if not loja and not self.mock:
            raise ValueError("PAN_LOJA_ID não configurado")
        if self.mock:
            log.info("pan_preanalise_mock", cpf=mask_cpf(cpf), categoria=cat)
            # Resposta simulada determinística com base no último dígito do CPF
            digits = ''.join([c for c in cpf if c.isdigit()])
            aprovado = (len(digits) > 0 and int(digits[-1]) % 2 == 0)
            return {
                "ok": True,
                "status": 200,
                "data": {
                    "cpf": mask_cpf(cpf),
                    "categoriaVeiculo": cat,
                    "resultado": "APROVADO" if aprovado else "EM_ANALISE",
                    "limite_pre_aprovado": 50000 if aprovado else 0,
                },
                "mock": True,
            }
        token = self.obter_token()

        # Conforme documentação: GET /openapi/veiculos/v0/lojas/{idLoja}/preanalise?cpfCliente=...&categoriaVeiculo=...
        url = f"{self.base_url}/openapi/veiculos/v0/lojas/{loja}/preanalise"
        params = {"cpfCliente": cpf, "categoriaVeiculo": cat}
        headers = {
            "Authorization": f"Bearer {token}",
            "ApiKey": self.api_key,
        }
        with self._client() as client:
            resp = client.get(url, headers=headers, params=params)
        if resp.status_code == 401 or resp.status_code == 403:
            # tenta renovar token uma vez
            token = self.obter_token(force_refresh=True)
            headers["Authorization"] = f"Bearer {token}"
            with self._client() as client:
                resp = client.get(url, headers=headers, params=params)
        if resp.status_code >= 400:
            log.warning(
                "pan_preanalise_error",
                status=resp.status_code,
                cpf=mask_cpf(cpf),
                categoria=cat,
                body=resp.text[:500],
            )
            return {
                "ok": False,
                "status": resp.status_code,
                "message": "Não foi possível completar a pré‑análise agora.",
            }
        data = resp.json()
        log.info("pan_preanalise_ok", cpf=mask_cpf(cpf), categoria=cat)
        return {
            "ok": True,
            "status": resp.status_code,
            "data": data,
        }
