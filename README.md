# AtendeJá – Chatbot, Operações e Relatórios

> Vitrine técnica de um produto real com backend FastAPI + frontend React (Vite/TS), autenticação JWT, administração, importação de dados e dashboards. Código limpo, testes, logs estruturados e documentação.

## Destaques
- Autenticação JWT (login/logout) e gestão de usuários (admin/colaborador).
- Importação de imóveis via CSV com feedback na UI.
- Relatórios com ECharts (filtros por período/data/canal) servidos por endpoint dedicado de métricas.
- Webhooks e integrações de mensageria preparados (WhatsApp Cloud API / BSP) com camadas desacopladas.
- Qualidade: testes (pytest/vitest), logs estruturados (`structlog`), documentação e estilo git.

## Arquitetura e Stack
- Backend (`app/`):
  - FastAPI (Python 3.11), `uvicorn`, `pydantic`.
  - Autenticação JWT, autorização básica e seed de admin.
  - SQLAlchemy + Alembic (migrations) – atualmente usando SQLite local para dev; compatível com Postgres (ex.: Supabase).
  - Logs estruturados com `structlog` e middlewares de tracing leve.
  - Endpoints: saúde (`/health`), operações (`/ops`), domínio imobiliário (`/re`), admin (`/admin`), auth (`/auth`), métricas (`/metrics`).

- Frontend (`frontend/ui/`):
  - React 18 + Vite + TypeScript + Tailwind.
  - React Router 6, Auth util (`apiFetch` injeta Authorization).
  - Páginas: Login, Imóveis, Importar CSV, Relatórios (ECharts), Usuários (admin).

- Observabilidade e Operação:
  - Logs em JSON e padronização de erros.
  - Estrutura preparada para deploy em Render/Netlify (frontend) e Render/EC2 (backend).

## Funcionalidades Implementadas
- Autenticação e Autorização
  - Login JWT (`/auth/login`), `apiFetch` no front, guard de rotas (`RequireAuth`).
  - Página de usuários: criar/ativar/desativar/promover.

- Importação CSV (ND Imóveis)
  - Upload autenticado no frontend para `/admin/re/imoveis/import-csv` com mensagens de sucesso/erro.

- Relatórios (Dashboards)
  - Página `Reports` com 3 gráficos: Leads por mês, Conversas WhatsApp, Taxa de conversão.
  - Filtros rápidos (6/12 meses) e por data (`start_date`/`end_date`) e canal.
  - Backend `GET /metrics/overview` servindo dados (stub sintético pronto para ligar no banco).

- Integrações de Mensageria (preparadas)
  - Webhook base em `/webhook` (Meta Cloud API).
  - Camada de provider desacoplada para trocar Twilio/Meta com baixo impacto.

## Como rodar (dev)

### Backend
Pré-requisitos: Python 3.11 e `pip`.

```
# Windows (PowerShell)
$env:DATABASE_URL_OVERRIDE="sqlite:///./dev_auth.db"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-dir app --reload-dir tests
```

Swagger/OpenAPI: http://localhost:8000/docs

### Frontend
Pré-requisitos: Node 18+.

```
cd frontend/ui
npm install
npm run dev
# http://localhost:5173
```

### Testes
- Backend: `pytest -q`
- Frontend: `npm test` (vitest)

## Endpoints Principais (amostra)
- `GET /health` – liveness/readiness simples.
- `POST /auth/login` – autenticação JWT.
- `GET /auth/me` – dados do usuário logado.
- `POST /admin/re/imoveis/import-csv` – upload de CSV autenticado.
- `GET /metrics/overview?period_months=6|12&channel=whatsapp|all&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` – dados para dashboards.

## Qualidade e Boas Práticas
- Logs estruturados (`structlog`), middleware de acesso HTTP e erros padronizados.
- Configurações via `app/core/config.py` e variáveis de ambiente.
- Testes automatizados (backend e frontend) e fixtures em `tests/`.
- Estilo de commits e PRs coerentes. CI para frontend em `.github/workflows/frontend-ci.yml`.

## Documentação de Arquitetura
- `docs/ARCHITECTURE.md` – visão geral, componentes e escolhas técnicas.
- `docs/ARCHITECTURE-CHOICES.md` – trade-offs.
- `docs/SECURITY.md`, `docs/TESTING.md`, `docs/OPERATIONS.md` – guias práticos.

## Roadmap curto
- Conectar `GET /metrics/overview` ao banco (agregações reais).
- Webchat (canal sem custo por mensagem) com MCP + agente OpenAI.
- RBAC por papéis nas páginas (relatórios/admin) e auditoria básica.
- Observabilidade: métricas de app e traces leves.

## Licença
MIT/
