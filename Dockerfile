FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.8.3

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# Copia metadados do projeto (para cache de dependências mais eficiente)
COPY pyproject.toml .
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copiar código da aplicação
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY tests ./tests
COPY start.sh ./start.sh
RUN chmod +x ./start.sh

EXPOSE 8000

# Default command can be overridden em docker-compose
CMD ["./start.sh"]
