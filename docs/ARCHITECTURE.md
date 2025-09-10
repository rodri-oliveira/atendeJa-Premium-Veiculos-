# Arquitetura – AtendeJá Chatbot

## Visão Geral
Serviço de chatbot WhatsApp com foco em atendimento (v1) e marketing (v1.1), construído em torno de:

- API (`app/main.py`) com FastAPI: recebe webhooks e expõe endpoints admin/saúde.
- Fila (Celery + Redis): processamento assíncrono e orquestração determinística.
- Banco (PostgreSQL): persistência relacional, multi-tenant por `tenant_id`.
- Observabilidade: logs estruturados, healthchecks. Dashboards de negócio com Metabase (perfil opcional do Compose).

## Componentes
- `app/api/routes/`
  - `webhook.py`: verificação e recepção de eventos do WhatsApp Cloud API.
  - `health.py`: endpoints de liveness/readiness.
- `app/core/`
  - `config.py`: configurações via `.env` (Pydantic Settings).
  - `logging.py`: `structlog` com JSON.
- `app/workers/celery_app.py`: instância do Celery e tasks.
- `app/repositories/db.py`: engine do SQLAlchemy e `SessionLocal`.

## Fluxo Inbound (Atendimento)
1. WhatsApp chama `POST /webhook` com evento.
2. API valida, loga, normaliza e enfileira tarefa Celery (futuro: `process_incoming_event`).
3. Worker consome a fila e executa a state machine do atendimento, podendo:
   - Persistir contato/conversa/mensagem.
   - Decidir próxima ação (mensagem de resposta, mudança de estado).
   - Enfileirar envios outbound.

## Fluxo Outbound
1. Caso de uso solicita envio (texto/template/mídia).
2. Serviço de mensageria compõe o payload e chama WhatsApp Cloud API.
3. Registra idempotência, status e trata retries e DLQ em falhas transitórias.

## Multi-tenant
- Campo `tenant_id` nas principais tabelas para isolar clientes.
- Configurações por tenant (tokens, idioma preferencial) podem residir em tabela própria.

## Marketing (v1.1)
- Campanhas com opt-in/opt-out, segmentação por tags, template aprovado e variáveis.
- Throttling por tenant, agendamento e janela de envio.
- Métricas por campanha (enviadas/entregues/falhas) e painéis no Metabase.

## Segurança
- Verificação do webhook via `WA_VERIFY_TOKEN`.
- (Opcional) Validação de assinatura HMAC.
- Endpoints admin com autenticação (JWT) – a ser adicionado.

## Decisões (resumo)
- FastAPI, Celery, Redis, Postgres, SQLAlchemy 2.x, Alembic, structlog.
- Poetry para dependências, Docker Compose para dev e instalação.
- Metabase como dashboards de negócio (perfil `dashboards`).

Consulte `SECURITY.md` e `OPERATIONS.md` para detalhes operacionais e boas práticas.
