# Operação – AtendeJá Chatbot

## Subir/Parar serviços
- Subir (dev padrão):
```
docker compose up -d --build
```
- Parar:
```
docker compose down
```
- Logs em tempo real:
```
docker compose logs -f
```

## Variáveis de ambiente
- Copie `.env.example` para `.env` e ajuste conforme seu ambiente.
- Em produção, defina variáveis via ambiente/secret manager.

## Backup/Restore do Postgres
- Backup completo (dump):
```
docker exec -i atendeja-postgres pg_dump -U ${POSTGRES_USER:-atendeja} ${POSTGRES_DB:-atendeja} > backup.sql
```
- Restore:
```
cat backup.sql | docker exec -i atendeja-postgres psql -U ${POSTGRES_USER:-atendeja} -d ${POSTGRES_DB:-atendeja}
```
Scripts prontos em `infra/scripts/*` (Windows e Linux/macOS).

## Healthchecks
- API: `GET /health/live` e `GET /health/ready`
- Docker fará wait até Postgres/Redis ficarem saudáveis antes de subir API/Worker.

## Atualização de versão
- Atualize o código, gere nova imagem e suba novamente:
```
docker compose pull   # se usar imagens publicadas
# ou
docker compose build --no-cache

docker compose up -d
```

## Exposição pública (Webhooks em dev)
- Use ngrok ou Cloudflare Tunnel para expor `http://localhost:8000`.
- No Meta, configure Verify URL `http://SEU_HOST/webhook` e `WA_VERIFY_TOKEN`.

## Segurança básica
- Proteja `.env` e tokens.
- Em produção, considere usar HTTPS (proxy reverso) e secret manager.

