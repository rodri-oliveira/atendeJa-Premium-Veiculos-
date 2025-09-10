# Guia de Estilo

## Commits
- Use Commits Convencionais:
  - `feat(escopo): descrição`
  - `fix(escopo): descrição`
  - `docs(escopo): ...`, `chore`, `refactor`, `test`, `perf`
- Mensagens no imperativo, curtas e objetivas.

## Python
- Python 3.11, tipagem (mypy) sempre que possível.
- Formatação: `ruff format` (ou black compatível), linha máx. 100 colunas.
- Imports agrupados: stdlib, terceiros, locais.
- Funções curtas, responsabilidades claras. Trate erros com exceções específicas.

## FastAPI
- Rotas em `app/api/routes/` com `APIRouter` e `tags`.
- Schemas Pydantic em `app/schemas/` (a criar conforme evolução).
- Response models e validação sempre que possível.

## Logs
- `structlog` em JSON, sem registrar segredos.
- Inclua chaves úteis (tenant_id, message_id, task_id).

## Testes
- `pytest`, organização por unidade/integração.
- Cobertura nos fluxos críticos (webhook, envio, workers).
