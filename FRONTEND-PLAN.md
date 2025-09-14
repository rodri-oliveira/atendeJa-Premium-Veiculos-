
## Atualização — 13/09/2025

### Movimentos de hoje
- App Shell com `react-router-dom` criado (`src/layouts/AppShell.tsx`, rotas em `src/App.tsx`).
- Páginas:
  - `orders` (Kanban) com header sticky, botão "Atualizar agora" e colunas responsivas (clamp 280–360px).
  - `settings` (somente leitura) exibindo `config.json` efetivo.
  - `delivery` (stub inicial).
- RBAC mínimo (mock) com `AuthProvider` (`src/auth/provider.tsx`):
  - `LoginPage` com papéis operador/gerente e guarda de rota (`/settings` → gerente).
- UX do Drawer: validação de endereço (CEP/UF), máscara de CEP, e mensagens por campo.
- Cards exibem "Itens: N".
- GitHub Actions: otimizado e colocado em `workflow_dispatch` (manual) para evitar ruído durante o dev local.

### Problemas atuais e ações objetivas
- ESLint/TS nos fontes:
  - `src/pages/KanbanPage.tsx`:
    - [feito] regra `react-hooks/exhaustive-deps` normalizada com `useCallback`/deps corretas.
    - [feito] remoção de import não utilizado e `catch` tipado como `unknown` com `errMsg`.
  - `src/components/OrderDrawer.tsx`:
    - [feito] `any` → `unknown` nos `catch`; normalização de erro; aspas escapadas em texto.
  - `src/auth/provider.tsx`:
    - [feito] remoção de variáveis `err` não usadas e logs mínimos.
  - `src/lib/api.ts`:
    - [pendente] trocar `any` por `unknown` nos `catch` de `setOrderAddress`, `setOrderStatus`, `confirmOrder`.

- Config em dev (`/config.json` retornando HTML em Vite):
  - [feito] `ConfigProvider` valida `Content-Type` e usa `defaultConfig` quando não for JSON (log de aviso apenas).

- Login/redirect:
  - [feito] `RequireManager` envia `?from=` e `LoginPage` redireciona automaticamente para a rota de origem.

### Roadmap (2–4 semanas)
- RBAC completo:
  - Integração de login real (API), tokens e expiração.
  - Exibir usuário e botão "Sair" no `AppShell` (limpar sessão, voltar para `/login`).
- Observabilidade do front:
  - Instrumentar `src/lib/api.ts` com logs de latência/erros (sem vendor).
  - Boundary de erros global e mensagens amigáveis.
- Painel:
  - Sumário por coluna (contagem total e itens).
  - Estados e ações revisadas por `config.json` (hardening contra configuração inválida).
- Entregas (`/delivery`):
  - Lista de entregas ativas (stub → lista real) e filtros.
- Documentação/OPS (local-first):
  - `OPS.md` com "subir/derrubar", ver logs, backup/restore.
  - Scripts PowerShell: `start-local.ps1`, `stop-local.ps1`, `backup-db.ps1`, `restore-db.ps1`.

### Estratégia de Deploy
- Local-first (baixo custo para o cliente):
  - Docker Compose com `api`, `postgres`, `redis`, `web`.
  - `config.json`/`env.js` em runtime, sem rebuild.
  - Guia de backup/restore do Postgres e logs.
- Cloud opcional (quando houver demanda/escala):
  - Build/push de imagens (API/WEB) para registry.
  - `compose-prod.yml` com imagens versionadas e variáveis.
  - Workflow manual no Actions para deploy com aprovação.

# Plano do Frontend (Ops Kanban) — AtendeJá

## Visão Geral
- Objetivo: entregar uma UI operacional (Kanban) para monitorar e operar pedidos.
- Stack: React + TypeScript + Vite + Tailwind CSS.
- Execução: front servido por Nginx em um container separado (`web`) e API FastAPI no container `api`.
- Instalação simples via `docker-compose.yml` (na pasta `atendeja-chatbot/`).

## Arquitetura
- Diretórios principais:
  - `atendeja-chatbot/frontend/` (dentro deste repositório)
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
    context: ./frontend
    dockerfile: Dockerfile.web
  container_name: atendeja-web
  depends_on:
    api:
      condition: service_started
  ports:
    - "8082:80"
  volumes:
    - ./frontend/ui/public/env.js:/usr/share/nginx/html/env.js:ro
```
- Observação: serviços `api`, `worker`, `postgres`, `redis` e `adminer` já existem.

## Passo a passo para subir o front
1) Garanta que os arquivos existem:
   - `./frontend/Dockerfile.web`
   - `./frontend/nginx/nginx.conf`
   - `./frontend/ui/public/env.js` com `window.ENV.API_BASE_URL = '/api';`
2) A partir de `atendeja-chatbot/`:
```powershell
docker compose build web
docker compose up -d --no-deps --force-recreate web
```
3) Acesse: `http://localhost:8082`

## Desenvolvimento local do front (opcional, sem Docker)
- Para o IDE não mostrar erros de tipos, instale dependências localmente:
```powershell
pushd ./frontend/ui
npm install
npm run dev
popd
```
- A UI de dev sob Vite ficará em `http://localhost:5173`.
- Para a API, ajuste `public/env.js` para `http://localhost:8000` enquanto testar localmente.

## Troubleshooting
- "no configuration file provided: not found": execute comandos na pasta que contém `docker-compose.yml` (`atendeja-chatbot/`) ou use `-f` com o caminho do compose.
- "failed to read dockerfile": verifique `build.context` e `dockerfile` no compose. Com estrutura recomendada, `context: ./frontend` e `dockerfile: Dockerfile.web`.
- "... /ui/public/env.js: not found": crie `./frontend/ui/public/env.js` ou ajuste o caminho no Dockerfile se necessário.
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

## CI do Frontend
- Pipeline GitHub Actions em `.github/workflows/frontend-ci.yml` para rodar `npm ci`, `tsc --noEmit`, `npm run lint`, `npm run test` e `npm run build` na pasta `frontend/ui` em pushes/PRs.

## Decisões e mudanças (12/09/2025 - tarde)

- Fluxo de Rascunho:
  - A ação "Aguardando pagamento" no cartão não chama a API diretamente. Ela abre o `OrderDrawer` para validações.
  - No Drawer, adicionamos:
    - Botão "Confirmar pedido (Aguardando pagamento)" que executa `PATCH /orders/{id}?op=confirm`.
    - Formulário mínimo de endereço e ação `PATCH /orders/{id}?op=set_address`.
  - Motivo: a API exige endereço e loja aberta; confirmar direto do cartão gerava 400.
- Auto-refresh:
  - Pausamos o auto-refresh enquanto o Drawer está aberto e retomamos ao fechar (com small delay). Evita perda de foco ao editar endereço.
- Ações por etapa (configurável):
  - `frontend/ui/public/config.json` mapeia `kanban.actions` por status.
  - Estados terminais (`delivered`, `canceled`) não exibem ações no cartão, mesmo se configuradas por engano.
- Cache do config:
  - `nginx.conf` com `location = /config.json { Cache-Control: no-store }` para refletir alterações sem hard refresh.
- Layout das colunas:
  - Grid substituído por `flex-row` com `overflow-x-auto` e colunas com largura fixa (320px). Garante colunas lado a lado com scroll horizontal.
- Nomenclatura de colunas:
  - `out_for_delivery` → "Em rota"; `delivered` → "Finalizado".

## Próximos passos imediatos (Painel)

- Contagem de cartões no cabeçalho de cada coluna.
- Desabilitar botões na Kanban enquanto a chamada assíncrona estiver em andamento.
- Melhorar validação do endereço (CEP e UF) e feedback por campo.
- Testes: cobrir `confirmOrder` (sucesso e 400 address_required) e mapeamento de ações por `config.json`.

## Evolução para App Shell e rotas

- Introduzir `AppShell` com `Sidebar`/`Topbar` e `react-router-dom`.
- Rotas iniciais: `/dashboard`, `/orders` (Kanban), `/delivery`, `/menu`, `/customers`, `/settings`.
- Providers no shell: `ConfigProvider`, futuro `AuthProvider` e logger global.
- RBAC: perfis operador (Orders) e gerente (todas as rotas).

## Ajustes sugeridos no CI

- Adicionar cache do `~/.npm` (já habilitado via `actions/setup-node` com `cache: npm`).
- Rodar passos apenas quando arquivos em `frontend/ui/**` mudarem (paths-filter) para otimizar execuções.
- Publicar artefatos de build (`dist/`) como artifact do job (útil para previews).

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

---

## Atualização — 13/09/2025 (tarde)

### Situação atual (testes e UX)
- __Falhas em testes do Drawer__ (`frontend/ui/tests/order.drawer.test.tsx` e `tests/ptbr.regression.test.tsx`):
  - 404 em `GET /orders/1` durante render do Drawer devido a mocks concorrentes/global vs locais.
  - Caso "confirma pedido" não avançava para `pending_payment` quando GET inicial não possuía endereço completo.
- __UX Kanban__: responsividade real entregue (sem scale), modo compacto por tokens, colunas por alvo com clamp min/máx, preferências por `localStorage` e defaults por `public/config.json`.

### Ações imediatas (corrigir suíte)
- __Padronizar mocks por teste no Drawer__ (sem depender de `beforeEach` global):
  - Em cada `it` que monta o Drawer, definir `window.ENV = { API_BASE_URL: '/api' }` e `g.fetch` local cobrindo:
    - `GET` que inclua `/orders/1` (sem subpaths) → draft com dados válidos.
    - `GET /orders/1/events` → `[]`, `GET /orders/1/relation` → objeto básico, `GET /orders/1/reorders` → `[]`.
    - Usar `url.includes()` (tolerante a querystring/base).
  - No caso "confirma pedido...": mock __stateful__ único por teste (antes: draft com endereço completo; depois do `PATCH ?op=confirm`: `pending_payment`).
- __Teste pt-BR do Drawer__:
  - Limpar DOM e mocks (`vi.clearAllMocks(); vi.restoreAllMocks(); document.body.innerHTML=''`).
  - Container isolado e mocks abrangentes para `/orders/1` e sub-rotas.
  - Buscar elementos por `role`/`label` (acessibilidade) para estabilidade.

### Próximos 7 dias (prioridades)
- __RBAC real__ (alta): login via API, token + expiração, "Sair" no topo, guards por rota. Testes de login/expiração/logout.
- __Docs e OPS__: `docs/UX-GUIDELINES.md` (sem scale; densidade por tokens; colunas adaptativas; pt-BR; SPA fallback; config em runtime). `docs/OPS.md` + scripts PowerShell: `start-local.ps1`, `stop-local.ps1`, `rebuild-web.ps1`, `backup-db.ps1`, `restore-db.ps1`.
- __Entregas (/delivery)__: lista real com filtros simples; testes de renderização e filtro.

### Comandos mínimos (onde rodar)
- __Testes do front__
  - Pasta: `frontend/ui`
  - Comando: `npm test -s`
- __Dev server (hot reload)__
  - Pasta: `frontend/ui`
  - Comando: `npm run dev` → http://localhost:5173
- __Validar integrado no Nginx__
  - Pasta: raiz do projeto `atendeja-chatbot/`
  - Comandos:
    - `docker compose build web`
    - `docker compose up -d --no-deps --force-recreate web`
  - Acesso: http://localhost:8082
