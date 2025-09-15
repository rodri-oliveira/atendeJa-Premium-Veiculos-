# Arquitetura do MCP/Chatbot — Avaliação e Recomendações

Este documento resume uma avaliação honesta do caminho proposto (qualidade, simplicidade e baixo custo) e sugere pequenos ajustes para ficarmos com uma base sólida e barata.

## Proposta do Cliente (base)
- Agente IA: OpenAI GPT‑4 Turbo
- Infra: Render (containers backend + frontend)
- Banco: Supabase (Postgres gerenciado)
- Mensageria: Twilio WhatsApp API
- Orçamento estimado: ~R$ 231–260/mês (200 conversas/mês)

## Opinião técnica (resumo)
- Qualidade: boa, com ajustes no modelo e nos providers de mensageria.
- Simplicidade: alta (Render + Supabase + Twilio simplificam operações).
- Custo: dá para reduzir ainda mais sem perder qualidade.

## Recomendações pragmáticas

1. Modelos OpenAI (custo/qualidade)
- Preferir GPT‑4o‑mini como default (ótimo custo/benefício) e manter fallback para GPT‑4o/4‑Turbo quando necessário.
- Estratégias de economia:
  - Janelas de contexto menores + resumos de conversas.
  - Heurísticas locais (regex/intent simples) antes de chamar LLM (já iniciadas no MCP).
  - Cache de respostas (se aplicável ao conteúdo institucional).

2. Mensageria WhatsApp
- Twilio é simples, porém tem taxa adicional. Para reduzir custo, avaliar Meta WhatsApp Cloud API direta (sem intermediário). Prós/Contras:
  - Twilio: onboarding simples, métricas e suporte; custo maior.
  - Meta Cloud API: custo menor por conversa, porém exige algumas etapas de verificação/configuração e gerenciamento direto.
- Recomendação: iniciar com Twilio (time‑to‑market) e planejar um adapter para alternar para Meta Cloud posteriormente sem refatoração.

3. Banco de Dados
- Supabase Pro é ótimo se for usar: auth, storage, realtime e dashboard integrados.
- Se o uso for apenas Postgres, o Neon (serverless Postgres) costuma ser mais barato no início.
- Recomendação: manter Supabase se vamos usar pelo menos 2 features além do Postgres; caso contrário, considerar Neon para reduzir custo.

4. Hospedagem
- Render funciona bem e é simples. Alternativas: Railway, Fly.io, Azure Container Apps.
- Recomendação: manter Render; cuidar de healthchecks e cold starts. Construímos com Docker + Alembic, então portabilidade é tranquila.

5. Segurança/LGPD
- Consentimento LGPD já no lead (ok). Próximos:
  - Mascarar PII em logs, retenção limitada para conversas, opção de opt‑out e purge.
  - Secrets geridos pelo provider (Render/Supabase) e nunca no repo.

6. Observabilidade e Resiliência
- Logs estruturados com correlação por conversação/tenant.
- Sentry (ou similar) para exceptions.
- Rate limiting por tenant e budget cap de tokens.
- Idempotência no processamento de webhooks e retries exponenciais.

7. MCP (estado atual e próximos passos)
- Base estável: tools registradas, “auto” com heurísticas (quartos/preço), endpoints prontos.
- Próximos incrementais:
  - Whitelist de tools por tenant no MCP (já previsto).
  - Prompt templates com políticas de negócio e persona.
  - Mecanismo simples de memória curta (resumo de contexto em 2–3 turns) para reduzir tokens.
  - Testes E2E do MCP (inputs ↔ intents ↔ resultados) e limites de custo.

## Caminho sugerido (curto prazo)
1) Encapsular provider de WhatsApp com interface única (Twilio agora; Meta Cloud API no futuro).
2) Importador CSV (campos de integração já criados) e pipeline de imagens.
3) Staging de leads e normalizador com upsert.
4) Flag de custo do MCP por tenant (limite mensal) + métricas simples.
5) Testes automatizados (API + MCP) no CI.

## Conclusão
O caminho proposto é bom. Com pequenos ajustes (GPT‑4o‑mini por padrão, adapter de mensageria, e avaliar Neon vs Supabase conforme features), atingimos excelente equilíbrio entre qualidade, simplicidade e baixo custo — e mantemos liberdade para evoluir a arquitetura sem retrabalho.
