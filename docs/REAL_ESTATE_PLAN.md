# Plano de Reestruturação – Imobiliária (AtendeJá)

## Objetivos
- Simplificar e focar no domínio imobiliário (atendimento + marketing) com custo baixo.
- Entregar rapidamente um MVP funcional: cadastro/listagem de imóveis e leads; funil básico via WhatsApp.
- Preparar terreno para escalar: multi-tenant, storage de imagens e deploy em nuvem barata.

## Stack (MVP)
- Backend: FastAPI (Python 3.11)
- Banco: PostgreSQL (Neon/Railway em produção; Docker local)
- Imagens: Cloudflare R2 (S3 compatível) – iniciar aceitando URLs; upload com URL pré-assinada em etapa posterior
- Hospedagem API: Railway/Render (deploy via Docker)
- Logs: structlog (JSON)
- Filas: adiado para pós-MVP (evitar custo e complexidade)

## Modelagem de Dados
- re_properties: imóvel (tipo, finalidade, preço, localização, quartos etc.), ativo, timestamps
- re_property_images: imagens (url, chave de storage, capa, ordenação)
- re_amenities, re_property_amenities: amenidades e associação
- re_leads: lead com preferências e consentimento LGPD
- re_inquiries: consulta/interesse (buy/rent/question) por lead e imóvel
- re_visit_schedules: agendamentos de visita (requested/confirmed/canceled/done)

Índices principais: finalidade, tipo, cidade/estado, preço, ativo, quartos.

## Endpoints (MVP – PT-BR)
- POST /re/imoveis – cadastra imóvel
- GET  /re/imoveis – lista com filtros (finalidade, tipo, cidade, estado, preço, dormitórios)
- GET  /re/imoveis/{id} – obter imóvel
- PATCH /re/imoveis/{id} – atualizar parcial (inclui ativar/desativar)
- POST /re/imoveis/{id}/imagens – adicionar imagem (url, capa, ordem)
- GET  /re/imoveis/{id}/imagens – listar imagens
- GET  /re/imoveis/{id}/detalhes – imóvel consolidado com imagens (para o front)
- POST /re/leads – cadastrar lead (nome, telefone, email, origem, preferencias, consentimento_lgpd)
- GET  /re/leads – listar leads

Próximos:
- POST /re/inquiries, POST /re/visit-schedules

## Fluxo WhatsApp (MVP)
1) Bot pergunta: compra ou locação
2) Cidade e estado
3) Tipo (apto/casa)
4) Quartos
5) Faixa de preço
6) Salva lead + inquiry, retorna top N imóveis

Eventos de negócio (logs): lead.created, inquiry.created, visit.requested

## Deploy Barato
- Banco: Neon (free tier) – variável DATABASE_URL_OVERRIDE
- API: Railway/Render – build Dockerfile
- Storage Imagens: Cloudflare R2 – chaves via env (S3_ACCESS_KEY_ID/SECRET)

## Segurança e LGPD
- Consentimento em `re_leads.consent_lgpd`
- Minimizar dados pessoais no payload
- Segredos via env e não comitar `.env`

## Roadmap Curto
- Dia 1–2: endpoints MVP + funil básico no webhook
- Dia 3: upload de imagens via URL pré-assinada (opcional)
- Dia 4: testes básicos + deploy

## Limpeza do Projeto
- Remover domínio de pizzaria (rotas e testes)
- Manter mensageria/base necessária para WhatsApp

---

## Arquitetura MCP (Agente IA)
- Endpoint do agente: `POST /mcp/execute` (Auth Bearer) – entrada com `input`, `tenant_id` e lista de tools permitidas (`tools_allow`).
- Tools previstas (MVP):
  - `buscar_imoveis(params)` – usa `GET /re/imoveis`.
  - `detalhar_imovel(imovel_id)` – usa `GET /re/imoveis/{id}` + `GET /re/imoveis/{id}/imagens`.
  - `criar_lead(dados)` – usa `POST /re/leads`.
  - `calcular_financiamento({preco, entrada_pct, prazo_meses, taxa_pct})` – cálculo local.
  - (próximas) `agendar_visita`, `enviar_campanha` (respeitando opt-in LGPD e templates aprovados).
- Roteamento no webhook por flag: `MCP_ENABLED=true` delega interpretação ao MCP; fallback para funil determinístico em caso de falha.
- Políticas: whitelist de tools por tenant, logs estruturados (`mcp.request`, `mcp.tool_call`, `mcp.response`), evitar dados sensíveis.

### Modo Auto (heurísticas MVP)
- Extrai intenção (comprar/alugar), tipo (apartamento/casa), cidade/UF (ex.: São Paulo/SP).
- Extrai dormitórios a partir de “2 quartos”/“2 dorm”.
- Extrai preço a partir de “até 3500”, “2000-3500” ou número solto “3500” (teto).

## Ingestão de Leads Multi‑Fonte
- Webhooks por fonte: `POST /integrations/leads/{fonte}` (ex.: `meta`, `google`, `portalX`).
- Staging: tabela `staging_leads` com payload bruto, `external_lead_id`, `source`, `received_at` e `processed_at`.
- Normalização: upsert em `re_leads` por `(tenant_id, source, external_lead_id)`, com `updated_at_source` para decidir atualização.
- Deduplicação/Merge: por telefone (E.164), email (lower) e `wa_id`. Preservar histórico em `conversation_events`.
- Orquestração de contato: tentar WhatsApp conforme janela do tenant; N tentativas; registrar `lead.created`, `contact.attempted`, `contact.replied`.

### Exemplo de payload normalizado (interno)
```json
{
  "source": "meta",
  "external_lead_id": "1234567890",
  "name": "Fulano",
  "phone": "+5511999990000",
  "email": "fulano@exemplo.com",
  "preferences": {"finalidade": "sale", "cidade": "São Paulo", "tipo": "apartment", "dormitorios": 2, "preco_max": 400000},
  "external_property_id": "X-42",
  "updated_at_source": "2025-09-14T18:00:00Z"
}
```

## Contratos para o Front (referência)
- Listar imóveis: `GET /re/imoveis`
  - Query: `finalidade`, `tipo`, `cidade`, `estado`, `preco_min`, `preco_max`, `dormitorios_min`, `limit`, `offset`.
  - Resposta: lista de `{ id, titulo, tipo, finalidade, preco, cidade, estado, bairro, dormitorios, banheiros, suites, vagas, ativo }`.
- Detalhar imóvel: `GET /re/imoveis/{id}` + `GET /re/imoveis/{id}/imagens`.
- Criar lead: `POST /re/leads` com `{ nome, telefone, email, origem, preferencias, consentimento_lgpd }`.

## Flags/Config (env)
- `APP_ENV`, `API_HOST`, `API_PORT`, `DEFAULT_TENANT_ID`.
- WhatsApp: `WA_VERIFY_TOKEN`, `WA_TOKEN`, `WA_PHONE_NUMBER_ID`, `WA_API_BASE`, `WA_WEBHOOK_SECRET`.
- DB/Redis: `DATABASE_URL_OVERRIDE` (preferir para produção), `POSTGRES_*`, `REDIS_*` (opcional no MVP).
- Storage: `STORAGE_PROVIDER=s3`, `S3_*` (quando ativarmos upload).
- MCP: `MCP_ENABLED`, `MCP_TOOLS_WHITELIST`.
- Imóveis somente leitura (produção): `RE_READ_ONLY=true` (bloqueia POST/PATCH de imóveis; usar importação/sync).

## Migrações (Alembic) – Procedimento com Docker
- Inicializar (uma vez, dentro do container): `docker compose exec api alembic init migrations`
- Ajustes feitos no repo:
  - `migrations/env.py` usa `settings.DATABASE_URL` e `CoreBase.metadata` (resiliente ao logging).
  - `alembic.ini` com `script_location=/app/migrations` dentro do container.
- Gerar revisão automática (exemplo):
  - `docker compose exec api alembic -c /app/alembic.ini revision --autogenerate -m "mensagem"`
- Aplicar:
  - `docker compose exec api alembic -c /app/alembic.ini upgrade head`
- Observação: Em rebuild da imagem, copie `migrations/` e `alembic.ini` para o container, se necessário:
  - `docker cp .\migrations atendeja-api:/app/`
  - `docker cp .\alembic.ini atendeja-api:/app/alembic.ini`

## Importação de Imóveis (preparação)
- Campos adicionados em `re_properties` para integração/sync:
  - `external_id` (string), `source` (string), `updated_at_source` (datetime)
  - Índice único por `(tenant_id, external_id)`.
- Próximo: endpoint admin `POST /admin/re/imoveis/import-csv` com upsert por `external_id` e parse de `imagens_urls` (separadas por `;`).

## Deploy
- Local: `docker compose up -d --build postgres api` (opcional `adminer`).
- Produção barata: API no Railway/Render; DB no Neon; imagens no Cloudflare R2 (quando necessário).
