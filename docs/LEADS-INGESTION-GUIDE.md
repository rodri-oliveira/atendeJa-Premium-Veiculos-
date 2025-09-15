# Guia de Ingestão de Leads — ND Imóveis

Este documento esclarece, de forma objetiva, como o produto lida com LEADS hoje, quais fluxos estão implementados e quais são as recomendações para integrações reais (Instagram, Facebook/Ads, Portais, WhatsApp etc.).

## Visão geral

- A criação/atualização de leads acontece via API do backend (sem UI para importação de leads).
- A listagem e visualização de leads acontece no frontend (página `Leads`).
- Importação por CSV está implementada apenas para IMÓVEIS. Para leads, recomendamos integrações por API (staging). A importação CSV de leads poderá ser adicionada quando houver demanda concreta.

## O que está implementado hoje

### 1) Upsert de leads por integrações (recomendado)

Endpoint: `POST /re/leads/staging`

- Deduplicação por `phone`; fallback por `email`.
- Rastreabilidade: `external_lead_id` e `updated_at_source` são gravados em `preferences`.
- `preferences` pode conter filtros desejados pelo lead (ex.: finalidade, cidade, tipo etc.).

Exemplo de payload:
```json
{
  "external_lead_id": "X-42",
  "source": "portalA",
  "name": "Fulano de Tal",
  "phone": "+5511999990000",
  "email": "fulano@exemplo.com",
  "preferences": { "finalidade": "sale", "cidade": "São Paulo", "tipo": "apartment" },
  "updated_at_source": "2025-09-15T12:05:00Z"
}
```

### 2) Criação manual (simples)

Endpoint: `POST /re/leads`

- Cadastro direto, sem a lógica de deduplicação do staging.
- Útil para entradas pontuais.

### 3) Listagem

Endpoint: `GET /re/leads`

- Consumido pela página `Leads` do frontend.
- A UI exibe chips para chaves comuns em `preferences` (ex.: finalidade, cidade, tipo) e permite expandir o JSON completo.
- Paginação: `limit` e `offset` (offset persistido na URL).

## O que NÃO está implementado (por decisão)

### Importação de leads por CSV (UI/Backend)

- A página “Importar CSV” foi entregue para IMÓVEIS, não para leads.
- Para leads, manteremos ingestão por **API staging** (melhor para múltiplas fontes, dedup e rastreabilidade).
- Quando houver demanda de CSV de leads, o plano sugerido (MVP):
  - Backend: `POST /admin/re/leads/import-csv` que lê o CSV e chama internamente a mesma lógica de staging.
  - Colunas sugeridas: `name, phone, email, source, preferencias_json, external_lead_id, updated_at_source, consent_lgpd`.
  - Front: página simples (análoga à de imóveis) com resumo/erros.

## Boas práticas para conectores externos (IG/Facebook/Ads/Portais/WhatsApp)

- **Contrato único de entrada**: sempre mapear dados da fonte e chamar `POST /re/leads/staging`.
- **Idempotência**: usar `external_lead_id + source`; na ausência, `phone` e `email`.
- **Rastreabilidade**: preencher sempre `external_lead_id` e `updated_at_source`.
- **Normalização (incremento futuro)**:
  - Telefone em E.164 (ex.: `+5511999990000`).
  - Validação de email.
- **LGPD**: quando a fonte trouxer consentimento, enviar `consent_lgpd` (hoje usado no `POST /re/leads`).
- **Observabilidade**: logs com `source`, `external_lead_id` e resultado do upsert.

## Reflexos no Frontend

- Página `Leads` é de **consulta**, não de importação.
- Página `Importar CSV` é apenas para **Imóveis**.
- Paginação e contadores visuais ajudam a operação; chips de `preferences` facilitam leitura rápida.

## Próximos passos sugeridos (quando houver demanda)

1. Normalização/validação no staging (telefone e email).
2. Importador CSV de leads (MVP), caso apareça necessidade de planilha.
3. Conectores específicos (workers/adapters) mapeando fontes externas para o staging.

---

Este guia reflete a arquitetura atual e a melhor prática para o projeto: staging como faixa de entrada única para leads de múltiplas fontes, UI de leads somente para consulta, e import por CSV focado em imóveis neste momento.
