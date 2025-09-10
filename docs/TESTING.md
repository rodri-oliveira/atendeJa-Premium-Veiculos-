# Testes – AtendeJá Chatbot

## Objetivos
- Garantir estabilidade do core de atendimento (webhook, state machine, envio).
- Evitar regressões com cobertura mínima em áreas críticas.

## Stack
- `pytest`, `pytest-asyncio`
- `mypy` (checagem estática) e `ruff` (lint/format)

## Como rodar
```
poetry install
pytest -q
```

## Estrutura de testes (sugerida)
- `tests/unit/` – funções puras, serviços de domínio, validação de schemas.
- `tests/integration/` – simulação de `POST /webhook`, jobs Celery, integração com repositórios.

## Dicas
- Use fixtures para sessão de banco (transacional) e para cliente HTTP da FastAPI.
- Mock de chamadas HTTP para WhatsApp Cloud API (httpx mockado).
- Assegure idempotência: reprocessar o mesmo evento não deve duplicar efeitos.
