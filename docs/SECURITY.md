# Segurança – AtendeJá Chatbot

## Webhook Verification
- O endpoint `GET /webhook` verifica `hub.verify_token` contra `WA_VERIFY_TOKEN`.
- Em produção, utilize URL com HTTPS por trás de um proxy reverso.

## Tokens e Segredos
- Nunca commitar `.env`. Use `.env.example` como referência.
- Em produção, prefira Secret Manager (ou variáveis de ambiente do orquestrador).
- Rotacione `WA_TOKEN` periodicamente conforme boas práticas.

## Rate Limiting e Proteções
- Endpoints admin devem exigir autenticação (JWT/OAuth) – item planejado no roadmap v1.
- Considere rate limiting via proxy (ex.: NGINX/Traefik) para rotas públicas.

## Auditoria e Logs
- Logs estruturados (JSON) com correlação de requisições e jobs.
- Não logar tokens/segredos. Sanitizar payloads sensíveis.

## Backups
- Rotina de backup/restore do Postgres descrita em `OPERATIONS.md` e scripts em `infra/scripts/*`.

## Dependências
- Atualizações regulares e checagem de vulnerabilidades (dependabot/renovate).

