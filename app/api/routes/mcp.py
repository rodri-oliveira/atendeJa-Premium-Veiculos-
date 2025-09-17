from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.repositories.db import SessionLocal
from app.core.config import settings
from app.integrations.pan import PanService
import structlog

router = APIRouter()
log = structlog.get_logger()


# --- Dep ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Schemas ---

class MCPRequest(BaseModel):
    input: str = Field(..., description="Entrada do usuário (texto livre)")
    tenant_id: str = Field(default_factory=lambda: settings.DEFAULT_TENANT_ID)
    tools_allow: Optional[List[str]] = Field(default=None, description="Lista de tools permitidas (whitelist)")
    mode: str = Field(default="auto", description="auto|tool")
    tool: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "input": "",
                    "mode": "tool",
                    "tool": "calcular_financiamento",
                    "params": {"preco": 400000, "entrada_pct": 20, "prazo_meses": 360, "taxa_pct": 1.0}
                },
                {
                    "input": "",
                    "mode": "tool",
                    "tool": "pan_pre_analise",
                    "params": {"cpf": "00000000000", "categoria": "USADO"}
                },
                {
                    "input": "",
                    "mode": "tool",
                    "tool": "pan_gerar_token",
                    "params": {}
                }
            ]
        }
    }


class MCPToolCall(BaseModel):
    tool: str
    params: Dict[str, Any]
    result: Any


class MCPResponse(BaseModel):
    message: str
    tool_calls: List[MCPToolCall] = []


# --- Auth ---

def _check_auth(authorization: Optional[str]):
    if not settings.MCP_API_TOKEN:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_token")
    token = authorization.split(" ", 1)[1]
    if token != settings.MCP_API_TOKEN:
        raise HTTPException(status_code=401, detail="invalid_token")


"""
Tools do domínio de imóveis ficam opcionais e só são registradas quando
REAL_ESTATE_ENABLED=true, evitando confusão no POC de veículos.
"""
def _build_realestate_tools():
    if not settings.REAL_ESTATE_ENABLED:
        return {}
    from app.domain.realestate.models import (
        Property,
        PropertyImage,
        PropertyType,
        PropertyPurpose,
        Lead,
    )

    def t_buscar_imoveis(db: Session, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        stmt = select(Property).where(Property.is_active == True)  # noqa: E712
        m = params or {}
        if m.get("finalidade"):
            stmt = stmt.where(Property.purpose == PropertyPurpose(m["finalidade"]))
        if m.get("tipo"):
            stmt = stmt.where(Property.type == PropertyType(m["tipo"]))
        if m.get("cidade"):
            stmt = stmt.where(Property.address_city.ilike(m["cidade"]))
        if m.get("estado"):
            stmt = stmt.where(Property.address_state == m["estado"]) 
        if m.get("preco_min") is not None:
            stmt = stmt.where(Property.price >= float(m["preco_min"]))
        if m.get("preco_max") is not None:
            stmt = stmt.where(Property.price <= float(m["preco_max"]))
        if m.get("dormitorios_min") is not None:
            stmt = stmt.where(Property.bedrooms >= int(m["dormitorios_min"]))
        limit = int(m.get("limit", 5))
        stmt = stmt.limit(min(max(limit,1), 20))
        rows = db.execute(stmt).scalars().all()
        return [
            {
                "id": r.id,
                "titulo": r.title,
                "tipo": r.type.value,
                "finalidade": r.purpose.value,
                "preco": r.price,
                "cidade": r.address_city,
                "estado": r.address_state,
                "dormitorios": r.bedrooms,
            }
            for r in rows
        ]

    def t_detalhar_imovel(db: Session, imovel_id: int) -> Dict[str, Any]:
        p = db.get(Property, imovel_id)
        if not p:
            raise HTTPException(status_code=404, detail="property_not_found")
        imgs_stmt = (
            select(PropertyImage)
            .where(PropertyImage.property_id == imovel_id)
            .order_by(PropertyImage.is_cover.desc(), PropertyImage.sort_order.asc(), PropertyImage.id.asc())
        )
        imgs = db.execute(imgs_stmt).scalars().all()
        return {
            "id": p.id,
            "titulo": p.title,
            "descricao": p.description,
            "tipo": p.type.value,
            "finalidade": p.purpose.value,
            "preco": p.price,
            "cidade": p.address_city,
            "estado": p.address_state,
            "bairro": p.address_neighborhood,
            "dormitorios": p.bedrooms,
            "banheiros": p.bathrooms,
            "suites": p.suites,
            "vagas": p.parking_spots,
            "area_total": p.area_total,
            "area_util": p.area_usable,
            "imagens": [
                {"id": i.id, "url": i.url, "is_capa": i.is_cover, "ordem": i.sort_order} for i in imgs
            ],
        }

    def t_criar_lead(db: Session, dados: Dict[str, Any]) -> Dict[str, Any]:
        lead = Lead(
            tenant_id=1,
            name=dados.get("nome"),
            phone=dados.get("telefone"),
            email=dados.get("email"),
            source=dados.get("origem", "mcp"),
            preferences=dados.get("preferencias"),
            consent_lgpd=bool(dados.get("consentimento_lgpd", False)),
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return {"id": lead.id, "nome": lead.name, "telefone": lead.phone}

    return {
        "buscar_imoveis": {"fn": t_buscar_imoveis},
        "detalhar_imovel": {"fn": t_detalhar_imovel},
        "criar_lead": {"fn": t_criar_lead},
    }


def t_calcular_financiamento(params: Dict[str, Any]) -> Dict[str, Any]:
    # Fórmula de parcela (Price): A = P * i / (1 - (1+i)^-n)
    preco = float(params.get("preco", 0))
    entrada_pct = float(params.get("entrada_pct", 20)) / 100.0
    prazo_meses = int(params.get("prazo_meses", 360))
    taxa_pct = float(params.get("taxa_pct", 1.0)) / 100.0 / 12.0
    principal = max(preco * (1 - entrada_pct), 0)
    if taxa_pct <= 0 or prazo_meses <= 0:
        return {"parcela": None, "principal": principal}
    parcela = principal * taxa_pct / (1 - (1 + taxa_pct) ** (-prazo_meses))
    return {
        "principal": round(principal, 2),
        "parcela": round(parcela, 2),
        "prazo_meses": prazo_meses,
        "taxa_mes": round(taxa_pct * 100, 4),
    }


# --- Tools: Banco Pan ---
def t_pan_gerar_token() -> Dict[str, Any]:
    svc = PanService()
    token = svc.obter_token(force_refresh=True)
    return {"ok": True, "token_preview": token[:8] + "..." if token else ""}


def t_pan_pre_analise(params: Dict[str, Any]) -> Dict[str, Any]:
    cpf = str(params.get("cpf", "")).strip()
    categoria = (params.get("categoria") or params.get("categoriaVeiculo") or None)
    if not cpf:
        raise HTTPException(status_code=400, detail="cpf_required")
    svc = PanService()
    res = svc.pre_analise(cpf=cpf, categoria=categoria)
    return res


TOOLS: Dict[str, Dict[str, Any]] = {
    # Gerais
    "calcular_financiamento": {"fn": t_calcular_financiamento},
    # Banco Pan
    "pan_gerar_token": {"fn": t_pan_gerar_token},
    "pan_pre_analise": {"fn": t_pan_pre_analise},
}

# Adiciona tools do domínio imobiliário somente quando habilitado
TOOLS.update(_build_realestate_tools())


def _whitelist_ok(name: str, allow: Optional[List[str]]) -> bool:
    if not allow:
        return True
    return name in allow


@router.post(
    "/execute",
    response_model=MCPResponse,
    summary="Executa agente MCP (MVP)",
    description="Modo auto interpreta o texto do usuário; modo tool executa uma ferramenta específica. Use Authorization: Bearer <token> se MCP_API_TOKEN estiver definido."
)
def execute_mcp(body: MCPRequest, db: Session = Depends(get_db), Authorization: Optional[str] = Header(default=None)):
    _check_auth(Authorization)

    tool_calls: List[MCPToolCall] = []

    # Modo explícito de tool
    if body.mode == "tool":
        if not body.tool:
            raise HTTPException(status_code=400, detail="tool_required")
        if not _whitelist_ok(body.tool, body.tools_allow):
            raise HTTPException(status_code=403, detail="tool_not_allowed")
        if body.tool not in TOOLS:
            raise HTTPException(status_code=404, detail="tool_not_found")
        fn = TOOLS[body.tool]["fn"]
        try:
            if body.tool == "detalhar_imovel":
                res = fn(db, int((body.params or {}).get("imovel_id")))
            elif body.tool == "calcular_financiamento":
                res = fn(body.params or {})
            elif body.tool == "buscar_imoveis":
                res = fn(db, body.params or {})
            elif body.tool == "criar_lead":
                res = fn(db, body.params or {})
            elif body.tool == "pan_gerar_token":
                res = fn()
            elif body.tool == "pan_pre_analise":
                res = fn(body.params or {})
            else:
                res = None
        except HTTPException:
            raise
        except Exception as e:
            log.error(
                "mcp_tool_error",
                tool=body.tool,
                error=str(e),
            )
            # Retorna erro claro ao cliente sem 500 genérico
            raise HTTPException(status_code=400, detail={"tool": body.tool, "error": str(e)})
        tool_calls.append(MCPToolCall(tool=body.tool, params=body.params or {}, result=res))
        return MCPResponse(message="tool_executed", tool_calls=tool_calls)

    # Modo auto (heurística melhorada – MVP)
    text = body.input.lower()
    if any(k in text for k in ["financi", "parcela", "juros"]):
        res = t_calcular_financiamento({"preco": 400000, "entrada_pct": 20, "prazo_meses": 360, "taxa_pct": 1.0})
        tool_calls.append(MCPToolCall(tool="calcular_financiamento", params={}, result=res))
        return MCPResponse(message=f"Parcela aproximada R$ {res['parcela']}", tool_calls=tool_calls)

    # Se domínio de imóveis estiver desabilitado, não tente rotas/imobiliário
    if not settings.REAL_ESTATE_ENABLED:
        return MCPResponse(
            message=(
                "Sou um assistente de financiamento de veículos. Você pode enviar: 'cpf 00000000000' e opcionalmente 'categoria USADO/NOVO/MOTOS'."
            ),
            tool_calls=tool_calls,
        )

    # Busca por intenção + extração de critérios (somente quando imóveis estiver habilitado)
    params: Dict[str, Any] = {}
    if "alugar" in text or "loca" in text:
        params["finalidade"] = "rent"
    if "comprar" in text or "compra" in text or "venda" in text:
        params["finalidade"] = "sale"
    if "apart" in text:
        params["tipo"] = "apartment"
    if "casa" in text:
        params["tipo"] = "house"
    # cidade/estado heurística simples
    if "sao paulo" in text or "são paulo" in text:
        params["cidade"] = "São Paulo"
        params["estado"] = "SP"

    import re
    m_quartos = re.search(r"(\d+)\s*(quarto|quart|dorm)", text)
    if m_quartos:
        try:
            params["dormitorios_min"] = int(m_quartos.group(1))
        except Exception:
            pass

    t_clean = text.replace("r$", "").replace(" ", "")
    if "-" in t_clean:
        parts = t_clean.split("-", 1)
        try:
            min_p = float(re.sub(r"[^0-9]", "", parts[0]))
            max_p = float(re.sub(r"[^0-9]", "", parts[1]))
            params["preco_min"] = min_p
            params["preco_max"] = max_p
        except Exception:
            pass
    m_ate = re.search(r"at[eé]?(\d{3,6})", t_clean)
    if m_ate:
        try:
            params["preco_max"] = float(m_ate.group(1))
        except Exception:
            pass
    elif not params.get("preco_max"):
        m_num = re.search(r"(\d{3,6})", t_clean)
        if m_num:
            try:
                params["preco_max"] = float(m_num.group(1))
            except Exception:
                pass

    # t_buscar_imoveis existe apenas quando REAL_ESTATE_ENABLED=True
    res = _build_realestate_tools().get("buscar_imoveis", {}).get("fn")
    if not res:
        return MCPResponse(message="Módulo de imóveis desabilitado.", tool_calls=tool_calls)
    data = res(db, params)
    tool_calls.append(MCPToolCall(tool="buscar_imoveis", params=params, result=data))
    if not data:
        return MCPResponse(message="Não encontrei imóveis com seu perfil. Pode me dizer cidade, tipo (apartamento/casa) e faixa de preço?", tool_calls=tool_calls)
    lines = ["Algumas opções:"]
    for r in data:
        lines.append(f"#{r['id']} - {r['titulo']} | R$ {r['preco']:,.0f} | {r['cidade']}-{r['estado']}")
    return MCPResponse(message="\n".join(lines), tool_calls=tool_calls)
