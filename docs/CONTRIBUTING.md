# Contribuição

## Fluxo de trabalho
- Use branches com prefixo: `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`.
- Commits convencionais (ex.: `feat(attendance): add state machine base`).
- PRs pequenos, com descrição e checklist de testes.

## Qualidade
- `ruff` para lint/format, `mypy` para tipos, `pytest` para testes.
- Pre-commit (a ser adicionado) para padronização automática.

## Padrões de código
- Python 3.11.
- Linhas até 100 colunas.
- Tipos sempre que possível (mypy).

## Testes
- Escreva testes para novas funcionalidades e correções de bugs.
- Mantenha cobertura em áreas críticas (webhook, envio, workers).
