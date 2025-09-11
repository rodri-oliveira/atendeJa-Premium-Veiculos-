# AtendeJá - Operações da API

Este documento descreve os fluxos operacionais e os endpoints principais da API, com bodies prontos para facilitar testes no Swagger (`http://localhost:8000/docs`).

- Serviços:
  - API: `http://localhost:8000`
  - Adminer (Postgres): `http://localhost:8080`

## Configuração do Tenant (Admin)

Endpoint: `PATCH /admin/tenant-settings`

Define parâmetros por tenant (padrão: `default`).

- Campos suportados:
  - `allow_direct_paid` (bool): permite pular direto para `paid` em alguns estados.
  - `auto_progress_enabled` (bool): liga/desliga automação de status por SLA.
  - `sla_preparo_min` (int): minutos para `paid -> in_kitchen`.
  - `sla_entrega_min` (int): minutos para `in_kitchen -> out_for_delivery`.
  - `sla_finalizacao_min` (int): minutos para `out_for_delivery -> delivered`.
  - `timezone` (str): ex.: `America/Sao_Paulo`.

Exemplos de body:

Modo manual (recomendado em operação real):
```json
{
  "allow_direct_paid": false,
  "auto_progress_enabled": false,
  "sla_preparo_min": 12,
  "sla_entrega_min": 25,
  "sla_finalizacao_min": 5,
  "timezone": "America/Sao_Paulo"
}
```

Modo demonstração (auto-avanço):
```json
{
  "allow_direct_paid": true,
  "auto_progress_enabled": true,
  "sla_preparo_min": 1,
  "sla_entrega_min": 1,
  "sla_finalizacao_min": 1,
  "timezone": "America/Sao_Paulo"
}
```

## Fluxo de Pedido (endpoints principais)

### 1) Criar pedido
`POST /orders`
```json
{
  "wa_id": "5511999999999",
  "first_item": {
    "menu_item_id": 1,
    "qty": 1,
    "options": { "size": "M" }
  },
  "notes": "Sem cebola"
}
```
Resposta: `{ "order_id": <id>, "status": "draft", ... }`

### 2) Adicionar item
`PATCH /orders/{order_id}?op=add_item`
```json
{
  "menu_item_id": 2,
  "qty": 1,
  "options": { "size": "G" }
}
```
Validação: `qty >= 1`, item precisa existir/estar disponível.

### 3) Definir endereço
`PATCH /orders/{order_id}?op=set_address`
```json
{
  "address": {
    "street": "Rua A",
    "number": "123",
    "district": "Centro",
    "city": "São Paulo",
    "state": "SP",
    "cep": "01312-000"
  }
}
```
Validação: CEP `^\d{5}-?\d{3}$`. Calcula `delivery_fee` automaticamente.

### 4) Confirmar
`PATCH /orders/{order_id}?op=confirm`
```json
{ "confirm": true }
```
Regras: loja precisa estar aberta (`rules.is_open_now` respeita `Tenant.timezone`).

### 5) Pagamento mock
- Gerar link/ID: `POST /orders/{order_id}/pay` (sem body)
- Confirmar pagamento (webhook): `POST /webhook/payments`
```json
{
  "order_id": 1,
  "payment_id": "UUID",
  "status": "paid"
}
```
Regras: aceita `pending_payment -> paid`. Se `allow_direct_paid=true`, aceita também `draft/in_kitchen/out_for_delivery -> paid` (com endereço).

### 6) Avançar status (manual)
`PATCH /orders/{order_id}/status`
- Iniciar preparo
```json
{ "status": "in_kitchen" }
```
- Saiu para entrega
```json
{ "status": "out_for_delivery" }
```
- Entregue
```json
{ "status": "delivered" }
```
- Cancelar (qualquer estágio permitido pela matriz)
```json
{ "status": "canceled" }
```

### 7) Consultar pedido
`GET /orders/{order_id}` (sem body)

## Automação por SLA

- Controlada pela flag `auto_progress_enabled` em `tenant-settings`.
- Quando habilitada:
  - `paid` (webhook) agenda `in_kitchen` em `sla_preparo_min`.
  - `in_kitchen` (API) agenda `out_for_delivery` em `sla_entrega_min`.
  - `out_for_delivery` (API) agenda `delivered` em `sla_finalizacao_min`.
- A automação usa a task Celery `orders.set_status` (`app/workers/tasks_orders.py`).

Pré-requisito: container do `worker` e broker (ex.: Redis) em execução.
- Verificar: `docker compose ps`
- Logs: `docker compose logs --no-color worker --tail=200`

## Mensageria WhatsApp

- Notificações de texto são enfileiradas em cada transição (`task_send_text`).
- Recomenda-se migrar para `send_template` com modelos padronizados.
- Para envio real, configurar `.env`: `WA_TOKEN`, `WA_PHONE_NUMBER_ID`.

## Padrão de Erros

Todas as respostas de erro seguem o formato:
```json
{ "error": { "code": "...", "message": "..." } }
```

Exemplos:
- Validação (422):
```json
{ "error": { "code": "validation_error", "message": "Erro de validação: body.address.cep" } }
```
- Loja fechada (400):
```json
{ "error": { "code": "store_closed", "message": "Loja fechada no momento." } }
```
- Transição inválida (400):
```json
{ "error": { "code": "invalid_transition:paid->paid", "message": "invalid transition:paid->paid" } }
```

## Observações Importantes

- `rules.is_open_now` usa o timezone do tenant e suporta janela que cruza meia-noite.
- Edição do pedido (itens/endereço) só é permitida em `draft`/`pending_payment`.
- O webhook de pagamento aceita `paid` uma única vez; chamadas repetidas retornam `invalid_transition:paid->paid`.
- Idempotência nos envios: `idempotency_key = "order-status-{order_id}-{status}"`.

## Roteiro Rápido (exemplo completo)

1. `POST /admin/tenant-settings` (modo demo):
```json
{
  "allow_direct_paid": true,
  "auto_progress_enabled": true,
  "sla_preparo_min": 1,
  "sla_entrega_min": 1,
  "sla_finalizacao_min": 1,
  "timezone": "America/Sao_Paulo"
}
```
2. `POST /orders` (criar pedido) – body no topo.
3. `PATCH /orders/{id}?op=add_item` – body no topo.
4. `PATCH /orders/{id}?op=set_address` – body no topo.
5. `PATCH /orders/{id}?op=confirm` – `{ "confirm": true }`.
6. `POST /orders/{id}/pay` – sem body; copie o `payment_id`.
7. `POST /webhook/payments` – com o `payment_id`.
8. `GET /orders/{id}` – acompanhar auto-avanço a cada ~1min.

---

Para dúvidas ou melhorias, consulte os arquivos:
- Rotas: `app/api/routes/*.py`
- Regras: `app/domain/pizza/rules.py`
- Workers: `app/workers/*.py`
- Erros: `app/api/errors.py`
