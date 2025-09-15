#!/bin/sh
set -e

# Executa migrações antes de iniciar a API
alembic -c /app/alembic.ini upgrade head

# Inicia a API
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
