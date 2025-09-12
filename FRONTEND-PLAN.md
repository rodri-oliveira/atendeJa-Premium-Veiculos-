# Plano do Frontend (Ops Kanban) — AtendeJá

## Visão Geral
- Objetivo: entregar uma UI operacional (Kanban) para monitorar e operar pedidos.
- Stack: React + TypeScript + Vite + Tailwind CSS.
- Execução: front servido por Nginx em um container separado (`web`) e API FastAPI no container `api`.
- Instalação simples via `docker-compose.yml` (na pasta `atendeja-chatbot/`).

## Arquitetura
- Diretórios principais:
  - `frontend/` (na raiz do monorepo, irmã de `atendeja-chatbot/`)
    - `ui/` — código do Vite/React/TS/Tailwind
      - `public/env.js` — injeta `window.ENV.API_BASE_URL` sem rebuild
      - `src/` — componentes, páginas e integração com API
    - `nginx/nginx.conf` — configuração para servir o build `dist/`
    - `Dockerfile.web` — build (Node) + runtime (Nginx)
  - `atendeja-chatbot/` — API (FastAPI), workers e `docker-compose.yml` que orquestra tudo

## Fluxo de Build e Runtime
1) Build:
   - `Dockerfile.web` (em `frontend/`) usa Node para executar `npm ci || npm install` e `npm run build` dentro de `frontend/ui`.
   - O output `dist/` é copiado para a imagem final baseada em `nginx:1.25-alpine`.
2) Runtime:
   - Nginx serve `dist/` na porta 80 do container `web`.
   - `env.js` é copiado para `/usr/share/nginx/html/env.js` e pode ser sobrescrito via volume no compose.
   - Reverse proxy no Nginx: `/api` → `http://api:8000` para chamadas de API via mesma origem (evita CORS e dependência de DNS do Docker no browser).
3) Comunicação front ↔ API:
   - No `docker-compose` os containers compartilham a rede. A API é acessível pelo hostname do serviço: `http://api:8000`.
   - No browser, a UI chama a API via mesma origem, usando `/api` (proxy do Nginx). `window.ENV.API_BASE_URL = '/api'`.

## Estrutura do Front (frontend/ui)
- `package.json` — dependências e scripts (dev, build, preview)
- `tsconfig.json` — config TypeScript
- `vite.config.ts` — config Vite
- `tailwind.config.js`, `postcss.config.js` — config Tailwind/PostCSS
- `index.html` — HTML base
- `public/env.js` — base URL da API
- `src/`:
  - `main.tsx`, `App.tsx`, `styles.css`
  - `lib/api.ts` — funções de integração com a API:
    - `listOrders({ status, search, limit, since, until })`
    - `setOrderStatus(orderId, next)`
  - `pages/KanbanPage.tsx` — colunas por status, filtros, auto-refresh
  - `components/OrderCard.tsx`, `components/FiltersBar.tsx`

## Endpoints da API usados pela UI
- `GET /orders` — listagem por coluna (status), com filtros `search`, `limit`, `since`, `until`
- `PATCH /orders/{id}/status` — ações rápidas por cartão
- (Fase 2) `GET /orders/{id}`, `GET /orders/{id}/events`, `GET /orders/{id}/relation`, `GET /orders/{id}/reorders`

## Configuração do Nginx (frontend/nginx/nginx.conf)
- Cache agressivo para assets versionados (js/css/imagens com hash)
- `index.html` com `Cache-Control: no-cache`
- Fallback SPA: `try_files $uri /index.html;`
- Reverse proxy: bloco `location /api/ { proxy_pass http://api:8000/; ... }` para chamadas à API na mesma origem

## Configuração do Dockerfile do Front (frontend/Dockerfile.web)
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY ui/ ./ui
WORKDIR /app/ui
RUN npm ci || npm install
RUN npm run build

FROM nginx:1.25-alpine
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/ui/dist/ /usr/share/nginx/html/
COPY ui/public/env.js /usr/share/nginx/html/env.js
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## docker-compose.yml (atendeja-chatbot/docker-compose.yml)
- Serviço `web`:
```yaml
web:
  build:
    context: ../frontend            # aponta para a pasta irmã
    dockerfile: Dockerfile.web
  container_name: atendeja-web
  depends_on:
    api:
      condition: service_started
  ports:
    - "8082:80"
  volumes:
    - ../frontend/ui/public/env.js:/usr/share/nginx/html/env.js:ro
```
- Observação: serviços `api`, `worker`, `postgres`, `redis` e `adminer` já existem.

## Passo a passo para subir o front
1) Garanta que os arquivos existem:
   - `../frontend/Dockerfile.web`
   - `../frontend/nginx/nginx.conf`
   - `../frontend/ui/public/env.js` com `window.ENV.API_BASE_URL = '/api';`
2) A partir de `atendeja-chatbot/`:
```powershell
docker compose build web
docker compose up -d --no-deps --force-recreate web
```
3) Acesse: `http://localhost:8082`

## Desenvolvimento local do front (opcional, sem Docker)
- Para o IDE não mostrar erros de tipos, instale dependências localmente:
```powershell
pushd ..\frontend\ui
npm install
npm run dev
popd
```
- A UI de dev sob Vite ficará em `http://localhost:5173`.
- Para a API, ajuste `public/env.js` para `http://localhost:8000` enquanto testar localmente.

## Troubleshooting
- "no configuration file provided: not found": execute comandos na pasta que contém `docker-compose.yml` (`atendeja-chatbot/`) ou use `-f` com o caminho do compose.
- "failed to read dockerfile": verifique `build.context` e `dockerfile` no compose. Com estrutura recomendada, `context: ../frontend` e `dockerfile: Dockerfile.web`.
- "... /ui/public/env.js: not found": crie `../frontend/ui/public/env.js` ou ajuste o caminho no Dockerfile se necessário.
- "npm ci ... package-lock.json": se não houver `package-lock.json`, o `npm ci` falha. O comando cai no `npm install`. Certifique-se de que `package.json` está presente em `frontend/ui`.
- CORS: não necessário no Docker Compose, pois o front chama `http://api:8000` dentro da rede dos serviços.

## Roadmap de UI
- Fase 1 (entregue):
  - Kanban com colunas por status, filtros, auto-refresh, ações de status.
- Fase 2:
  - Drawer de detalhes com itens, endereço, events, relation e reorders.
- Fase 3:
  - Badges de SLA (tempo excedido), paginação/scroll, preferências (localStorage).
- Fase 4 (opcional):
  - SSE/WebSocket para realtime, métricas de throughput na barra superior.

## Status Atual (12/09/2025)
- Estrutura do frontend recriada em `frontend/` com `ui/` (Vite/React/TS/Tailwind), `nginx/` e `Dockerfile.web`.
- Serviço `web` adicionado em `atendeja-chatbot/docker-compose.yml` para servir o build via Nginx na porta `8082`.
- Client HTTP inicial criado em `frontend/ui/src/lib/api.ts` com funções `listOrders` e `setOrderStatus`, alinhado aos contratos reais do backend.
- Testes unitários (Vitest + jsdom + RTL) configurados; testes do client em `frontend/ui/tests/api.test.ts`.
- Camada de i18n para status (en→pt-BR) em `frontend/ui/src/i18n/status.ts`.
- Página inicial `KanbanPage.tsx` criada e conectada ao `App` com auto-refresh e filtros básicos.
- Reverse proxy configurado no Nginx para `/api` → `http://api:8000` e `env.js` apontando para `/api`.

## Decisão Arquitetural Registrada
- Motivo: Em ambiente de browser, o hostname `api` não resolve fora da rede Docker. Para evitar CORS e dependência de DNS, adota-se reverse proxy no Nginx do `web` para `/api`.
- Impacto: Simplifica configuração de ambientes e evita erros de rede no front. O `env.js` permanece como mecanismo de configuração em runtime.

## Como rodar rapidamente
1) Docker (recomendado para validação rápida)
   - Diretório: `atendeja-chatbot/`
   - Comandos:
     ```powershell
     docker compose build web
     docker compose up -d web
     ```
   - Acessar: http://localhost:8082
2) Desenvolvimento local (sem Docker)
   - Diretório: `frontend/ui`
   - Comandos:
     ```powershell
     npm install
     npm run dev
     ```
   - Dev server: http://localhost:5173 (garanta `public/env.js` apontando para `http://localhost:8000`).

## Boas práticas adotadas
- Front isolado em `frontend/`, servindo build estático em Nginx.
  - API base configurável via `public/env.js` (sem rebuild por ambiente).
  - Compose único para subir a solução toda.
  - Código tipado e componentizado, com integração de API centralizada.

## Próximos passos (sugeridos)
- Pipeline CI (GitHub Actions) para build e testes do front (lint/tsc/build).
- Publicar assets do front em CDN (futuro) com cache global.
- Métricas/observabilidade do front (erro de rede, latências de chamada).
