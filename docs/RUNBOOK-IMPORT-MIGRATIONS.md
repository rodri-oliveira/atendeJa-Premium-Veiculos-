# Runbook: Importação CSV e Migrações (ND Imóveis)

Este runbook documenta boas práticas, passos e comandos para desenvolver, diagnosticar e operar o fluxo de importação CSV e o ciclo de migrações do banco de dados, garantindo estabilidade e rapidez na resolução de problemas.

## 1) Pré‑requisitos
- FastAPI com `UploadFile` exige a dependência: `python-multipart` (já adicionada em `pyproject.toml`).
- Dockerfile deve copiar `migrations/` e `alembic.ini` para a imagem (já ajustado).

## 2) Build & Health
- Rebuild API:
```powershell
docker compose up -d --build api
```
- Health básico:
```powershell
curl.exe http://localhost:8000/health/live
```
- Conferir rotas carregadas (OpenAPI):
```powershell
curl.exe http://localhost:8000/openapi.json | findstr /i "import-csv"
```

## 3) Migrações (Alembic)
- Aplicar migrações no container:
```powershell
docker compose exec api alembic -c /app/alembic.ini upgrade head
```
- Diagnóstico de desalinhamento (se erro de revisão desconhecida):
```powershell
docker compose exec postgres psql -U atendeja -d atendeja -c "SELECT * FROM alembic_version;"
```
- Ajustar versão manualmente (ex.: voltar para a inicial do repo):
```powershell
docker compose exec postgres psql -U atendeja -d atendeja -c "UPDATE alembic_version SET version_num='46ca38c65133';"
```
- Regenerar migração ausente (quando o modelo tem campos e o banco não):
```powershell
docker compose exec api alembic -c /app/alembic.ini revision --autogenerate -m "re_properties: add external_id/source/updated_at_source (regen)"
docker compose exec api alembic -c /app/alembic.ini upgrade head
```

## 4) Importação CSV
- Multipart (fluxo normal):
```powershell
curl.exe -v -F "file=@import_sample.csv;type=text/csv" http://localhost:8000/admin/re/imoveis/import-csv
```
- RAW (fallback/depuração):
```powershell
curl.exe -v -H "Content-Type: text/csv" --data-binary "@import_sample.csv" http://localhost:8000/admin/re/imoveis/import-csv-raw
```
- CSV esperado (headers):
```
titulo,descricao,tipo,finalidade,preco,condominio,iptu,cidade,estado,bairro,dormitorios,banheiros,suites,vagas,area_total,area_util,ano_construcao,external_id,source,updated_at_source,imagens_urls
```
- Observações do parser:
  - Remove BOM (\ufeff) se presente.
  - Normaliza headers para `lower().strip()`.
  - Imagens: primeira URL marcada como capa; separador `;`.
  - Upsert por `(tenant_id, external_id)`.

## 5) Diagnóstico Rápido
- Logs ao vivo:
```powershell
docker compose logs -f api
```
- Middleware de logs HTTP (já ativo):
  - `http_request_start` / `http_request_end`.
  - `http_request_exception` com traceback.
- Mensagens do importador:
  - `csv_import_request`, `csv_import_size`, `csv_import_headers` (multipart).
  - `csv_import_raw_size`, `csv_import_raw_headers` (raw).

## 6) Erros Comuns e Correções
- 400 genérico em multipart: verificar `python-multipart` instalado e content-type do curl.
- `UndefinedColumn (external_id)`: aplicar/gerar migração que cria colunas novas.
- Rota não encontrada: checar `openapi.json` e rebuild.
- “Empty reply from server”: verificar logs (`-f`), middleware HTTP e trace.

## 7) Comandos úteis
- Detalhes do imóvel (verificar dados após import):
```powershell
curl.exe http://localhost:8000/re/imoveis/1/detalhes
```
- Conferir head do Alembic:
```powershell
docker compose exec api alembic -c /app/alembic.ini heads
```
- Conferir versão atual aplicada:
```powershell
docker compose exec api alembic -c /app/alembic.ini current
```

## 8) Próximas melhorias (sugeridas)
- EntryPoint que roda `alembic upgrade head` antes do `uvicorn`.
- Testes automatizados mínimos: importador CSV, webhook (noop, idempotência), `/re/imoveis/{id}/detalhes`.

## 9) Checklist pós‑mudança
- Rebuild API.
- `GET /health/live` = 200.
- `openapi.json` contém as rotas novas.
- Import CSV (multipart) retorna 200 com `created/updated`.
- `/re/imoveis/{id}/detalhes` retorna campos e imagens esperados.
