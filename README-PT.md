# AtendeJá – Vitrine Técnica (One‑Pager)

[![Frontend CI](https://github.com/rodri-oliveira/atendeJA-ND-Imoveis-/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/rodri-oliveira/atendeJA-ND-Imoveis-/actions/workflows/frontend-ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal)
![React](https://img.shields.io/badge/React-18-61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Vite](https://img.shields.io/badge/Vite-5-646CFF)
![ECharts](https://img.shields.io/badge/ECharts-5-orange)
![JWT](https://img.shields.io/badge/Auth-JWT-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> Produto demonstrativo com foco em boas práticas: backend FastAPI + frontend React/Vite/TS, autenticação JWT, administração, importação CSV e dashboards com ECharts. Preparado para integrações de mensageria e MCP + agente de IA.

---

## Visão Geral
- __Autenticação & Admin__: login JWT, guarda de rotas, página de usuários (criar/promover/ativar).
- __Importar Imóveis__: upload CSV autenticado com feedback na UI.
- __Relatórios__: ECharts com filtros (6/12 meses, intervalo de datas, canal) a partir de `GET /metrics/overview`.
- __Mensageria__: webhook e camada de provider prontos para WhatsApp Cloud/BSP (ligação rápida ao agente MCP).
- __Qualidade__: testes (pytest/vitest), logs estruturados (structlog), documentação e CI de frontend.

## Arquitetura (alto nível)
```
React/Vite/TS (Tailwind) ──► FastAPI (JWT, SQLAlchemy, Alembic)
         ▲                          │
         │                          ├── /metrics (dashboards)
         │                          ├── /auth (login/me)
         │                          ├── /admin (gestão)
         │                          └── /webhook (mensageria)
    ECharts  ◄────────────────  Banco (SQLite dev / Postgres prod)
```

## Tecnologias principais
- __Backend__: FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic, Structlog
- __Frontend__: React 18, Vite, TypeScript, React Router, Tailwind, ECharts
- __Autenticação__: JWT (Bearer) com `apiFetch` injetando Authorization
- __Dados__: SQLite (dev) e compatível com Postgres (ex.: Supabase)

## Como rodar (dev)
- __API__ (Windows/PowerShell):
```powershell
$env:DATABASE_URL_OVERRIDE="sqlite:///./dev_auth.db"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-dir app --reload-dir tests
```
- __Frontend__:
```bash
cd frontend/ui
npm install
npm run dev   # http://localhost:5173
```

## Endpoints úteis
- `POST /auth/login`, `GET /auth/me`
- `POST /admin/re/imoveis/import-csv`
- `GET /metrics/overview?period_months=6|12&channel=whatsapp|all&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

## Screenshots (adicione suas imagens)
Coloque imagens em `docs/screenshots/` e referencie aqui:
- Login: `docs/screenshots/login.png`
- Importar CSV: `docs/screenshots/import.csv.png`
- Relatórios: `docs/screenshots/reports.png`

Exemplo de uso no Markdown:
```md
![Relatórios](docs/screenshots/reports.png)
```

## Diferenciais técnicos
- Camada de provider para mensageria (permite trocar Twilio/Meta com baixo impacto).
- Middlewares de logging e tratamento uniforme de erros.
- Dashboards com filtros e endpoint dedicado para métricas.
- Código organizado por domínio (`app/domain/realestate`, `app/api/routes/*`).

## Roadmap curto
- Conectar métricas a consultas reais no banco.
- Webchat (canal sem custo por mensagem) + MCP + agente OpenAI.
- RBAC por papéis e auditoria.

## Licença
MIT
