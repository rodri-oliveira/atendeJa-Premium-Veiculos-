# Roadmap

## v1 – Atendimento (prioridade)
- Webhook oficial WhatsApp (verificação + recepção)
- Enfileirar eventos (Celery) e base para state machine
- Envio (texto/template/mídia) com retries, idempotência e DLQ
- Modelo de dados inicial (tenants, contatos, conversas, mensagens, templates)
- Observabilidade (logs/health), testes e documentação

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

