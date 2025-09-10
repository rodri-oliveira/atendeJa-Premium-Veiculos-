# AtendeJá Chatbot

Chatbot WhatsApp profissional (Brasil) com FastAPI, Celery, Redis e PostgreSQL. Foco em atendimento robusto (v1) e marketing (v1.1), com arquitetura modular, documentação, testes e implantação via Docker.

## Principais recursos
- FastAPI com Swagger (OpenAPI) e endpoints de saúde (`/health/live`, `/health/ready`).
- Webhook do WhatsApp Cloud API (verificação e recepção).
- Filas com Celery + Redis; workers com retries e base para DLQ.
- PostgreSQL com SQLAlchemy + Alembic (migrations).
- Logs estruturados (JSON) via `structlog`.
- Deploy simples via `docker compose` (API, Worker, Redis, Postgres, Adminer). Perfil opcional: Metabase.

## Requisitos
- Docker e Docker Compose
- (Opcional para dev local) Python 3.11 + Poetry

## Configuração
1) Copie `.env.example` para `.env` e ajuste:
```
cp .env.example .env
```
Campos mínimos para testes com número de teste do WhatsApp (sem custo):
- `WA_VERIFY_TOKEN` (valor que você vai configurar no Meta para verificar o webhook)
- `WA_TOKEN` (token temporário do app do Meta)
- `WA_PHONE_NUMBER_ID` (ID do número de teste)

2) Suba os serviços (primeira vez pode demorar um pouco):
```
docker compose up -d --build
```
A API ficará em http://localhost:8000. Swagger: http://localhost:8000/docs

Adminer (Postgres GUI): http://localhost:8080
- System: PostgreSQL
- Server: postgres
- Username: atendeja
- Password: atendeja
- Database: atendeja

Metabase (opcional – perfil `dashboards`):
```
docker compose --profile dashboards up -d
```
Acesse http://localhost:3000 (configure um usuário e conecte ao Postgres: host `postgres`, db `atendeja`, user `atendeja`, pass `atendeja`).

## Webhook do WhatsApp Cloud API (teste grátis)
1) No Meta for Developers, crie um app e habilite o WhatsApp Cloud API.
2) Cadastre um Webhook apontando para:
- Verify URL: `http://<SEU_HOST>/webhook`
- Verify Token: o mesmo valor do `WA_VERIFY_TOKEN` do seu `.env`
Com ngrok ou Cloudflare Tunnel, exponha `http://localhost:8000` publicamente se estiver em dev.

3) Envio de mensagem de teste (número de teste):
- Use o painel do Meta para enviar ao seu número cadastrado como tester.
- Em breve aqui haverá um endpoint admin para enviar mensagens diretamente pela nossa API.

## Scripts (opcionais)
- Windows PowerShell: `infra/scripts/win/*.ps1` (start/stop/logs/backup/restore)
- Linux/macOS: `infra/scripts/nix/*.sh`

## Desenvolvimento local (opcional, sem Docker)
```
poetry install
uvicorn app.main:app --reload
celery -A app.workers.celery_app.celery worker --loglevel=INFO
```

## Documentação
- `ARCHITECTURE.md` – visão de componentes, fluxo inbound/outbound, filas, dados.
- `OPERATIONS.md` – como operar: start/stop/logs, backup/restore, atualização.
- `TESTING.md` – como rodar testes unitários e de integração.
- `SECURITY.md` – webhook verification, tokens, rate limiting.
- `CONTRIBUTING.md`, `STYLEGUIDE.md` – boas práticas de código e commits.
- `ROADMAP.md` – versões e entregas planejadas.

## Roadmap (resumo)
- v1 Atendimento: webhook oficial, state machine, envio com retries, persistência, testes e observabilidade.
- v1.1 Marketing: campanhas com opt-in, throttling, janela/agenda, métricas e Metabase.

## Licença
MIT
