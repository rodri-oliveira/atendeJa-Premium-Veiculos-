from __future__ import annotations
from fastapi import APIRouter, Query
from datetime import datetime, date

router = APIRouter()

MES_LABELS_PT = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
]


@router.get("/overview", summary="Métricas gerais (dados sintéticos para dashboard)")
async def metrics_overview(
    period_months: int = Query(6, ge=1, le=12, description="Período em meses (1 a 12)"),
    channel: str | None = Query(None, description="Canal a filtrar (ex.: 'whatsapp')"),
    start_date: date | None = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="Data final (YYYY-MM-DD)"),
):
    # Determina labels mensais conforme filtros
    labels: list[str]
    if start_date and end_date and start_date <= end_date:
        # Gera labels de mês/ano no intervalo
        labels = []
        cur = date(start_date.year, start_date.month, 1)
        endm = date(end_date.year, end_date.month, 1)
        while cur <= endm and len(labels) < 24:  # limite sanidade
            labels.append(MES_LABELS_PT[cur.month - 1])
            # avança um mês
            ny, nm = (cur.year + (cur.month // 12), 1 if cur.month == 12 else cur.month + 1)
            cur = date(ny, nm, 1)
        n = len(labels) if labels else 6
    else:
        n = 12 if period_months > 6 else 6
        labels = MES_LABELS_PT[:n]

    # Dados sintéticos; substitua por consulta real
    base_leads = [12, 18, 25, 22, 30, 28, 26, 29, 31, 27, 24, 33]
    base_conv = [80, 110, 95, 120, 130, 140, 135, 150, 145, 155, 160, 170]
    base_rate = [8, 9, 11, 10, 12, 13, 12, 13, 12, 14, 13, 15]
    leads = (base_leads * ((n // 12) + 1))[:n]
    conversas = (base_conv * ((n // 12) + 1))[:n]
    conversao = (base_rate * ((n // 12) + 1))[:n]

    if channel and channel.lower() != "whatsapp":
        conversas = [int(x * 0.9) for x in conversas]

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "labels": labels,
        "leads_por_mes": leads,
        "conversas_whatsapp": conversas,
        "taxa_conversao": conversao,
        "filters": {
            "period_months": period_months,
            "channel": channel,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    }
