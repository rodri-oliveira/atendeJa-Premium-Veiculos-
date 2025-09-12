# Roadmap

## DONE (Core)
- Webhook oficial WhatsApp (verificação + recepção) em `app/api/routes/webhook.py`
- Agregação inbound e normalização (Celery) em `app/workers/tasks_inbound.py`
- Outbound texto e template com retries/backoff e idempotência em `app/workers/tasks_outbound.py`
- Endpoints admin: handoff, envio (`/admin/send-text`, `/admin/send-template`), leitura (`/admin/conversations`, `/admin/messages`)
- Segurança: HMAC do webhook (`WA_WEBHOOK_SECRET`) e logs com redaction de segredos
- Testes: webhook, HMAC, outbound (HTTP mock via `respx`) — `pytest.ini` ajustado
- Dev: Docker Compose (api/worker/redis/postgres/adminer), lifespan FastAPI, health checks

## v1 – Atendimento (prioridade)
- Observabilidade (métricas básicas), testes e documentação complementares

## v1.0.1 – Segurança básica (produção)
- HMAC de webhook (validação de assinatura Meta)
- Redação de logs (PII/segredos) e RBAC simples para rotas admin
- Rate limiting por tenant/contato e backpressure de filas

## v1.Pizzaria/Lanches – MVP Vertical
- Domínio (tabelas): `customers`, `menu_items`, `orders`, `order_items`, `store_hours`, `delivery_zones`
- Fluxo conversacional (sem NLP): boas‑vindas → cardápio → montar pedido → endereço/taxa → pagamento (mock) → status
- Endpoints: `GET /menu`, `POST /orders`, `PATCH /orders/{id}`, `GET /orders/{id}`, `POST /orders/{id}/pay`, `PATCH /orders/{id}/status`
- WhatsApp Templates: menu, confirmação, link de pagamento, atualização de status
- Regras: horário de funcionamento, taxa por zona/CEP, ETA v1 heurístico (preparo + deslocamento + buffer)
- Testes: unit (regras) e E2E simulado (pedido completo)

## v1.Pagamentos – Integração real (opcional)
- Trocar provider mock por Mercado Pago/Pagar.me (link de pagamento) e processar webhooks

## v1.1 – Marketing
- Campanhas com opt‑in/opt‑out e segmentação por tags
- Throttling por tenant e janela de envio/agendamento
- Métricas de campanha e painéis no Metabase (perfil `dashboards`)

## v1.2 – Painel Operacional (opcional)
- UI web simples para conversas recentes, status, templates e reprocessamentos
- Auth de operadores e papéis básicos

## v1.3 – Observabilidade técnica ampliada
- Prometheus + Grafana (perfil opcional), métricas de fila e tempos

## v1.4 – Integrações
- Conectores (CRM/ERP) com adapters

## v1.Mídia – Suporte a imagens/documentos
- Inbound: download via WhatsApp Cloud API, validação MIME/tamanho
- Armazenamento em S3/MinIO (prod) e disco (dev), metadados em `media_assets`
- Outbound: envio de mídia por URL/media_id com retries e idempotência

## v1.Catálogo – Base de produtos para atendimento
- Tabelas `products` e `product_media` vinculadas a `media_assets`
- Endpoints admin para cadastro/associação de mídias
- Skill simples: consulta por atributos e envio de 3–5 imagens com descrição/preço

## Flexibilidade para outros segmentos (ex.: Petshop)
- Reaproveitar core WhatsApp/infra e camadas de conversas
- `MenuItem/Order/OrderItem` neutros com `options` para variações de serviço/produto
- Ajustar templates e regras específicas (ex.: taxa por peso, agendamento de serviços)

