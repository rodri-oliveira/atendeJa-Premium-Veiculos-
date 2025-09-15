import React, { useState } from 'react'

interface ImportResult {
  processed?: number
  inserted?: number
  updated?: number
  errors?: Array<{ line?: number; message: string }>
  [k: string]: any
}

export default function ImportCsv() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ImportResult | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setResult(null)
    if (!file) {
      setError('Selecione um arquivo CSV.')
      return
    }
    try {
      setLoading(true)
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch('/api/admin/re/imoveis/import-csv', {
        method: 'POST',
        body: fd,
      })
      if (!res.ok) {
        try {
          const js = await res.json()
          throw new Error(js?.detail || js?.message || `HTTP ${res.status}`)
        } catch {
          throw new Error(`HTTP ${res.status}`)
        }
      }
      const js = await res.json()
      setResult(js)
    } catch (e: any) {
      setError(e?.message || 'Falha no upload')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Importar CSV de Imóveis</h1>
        <div className="text-xs text-gray-500">Envie um arquivo .csv</div>
      </header>

      <form onSubmit={onSubmit} className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
        <div className="flex items-center gap-3">
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="text-sm"
          />
          <button
            type="submit"
            disabled={loading || !file}
            className="px-3 py-1.5 text-sm rounded bg-gray-900 text-white disabled:opacity-50"
          >
            {loading ? 'Enviando...' : 'Enviar'}
          </button>
        </div>
        <div className="text-xs text-gray-500">
          Dica: use o arquivo de exemplo disponível no repositório (import_sample.csv)
        </div>
      </form>

      {error && (
        <div className="text-sm text-red-600">Erro: {error}</div>
      )}

      {result && (
        <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-2">
          <h2 className="text-sm font-medium text-gray-900">Resultado</h2>
          <dl className="text-sm text-gray-700 grid grid-cols-2 sm:grid-cols-4 gap-2">
            {'processed' in result && (
              <div><span className="text-gray-500">Processados:</span> {String(result.processed)}</div>
            )}
            {'inserted' in result && (
              <div><span className="text-gray-500">Inseridos:</span> {String(result.inserted)}</div>
            )}
            {'updated' in result && (
              <div><span className="text-gray-500">Atualizados:</span> {String(result.updated)}</div>
            )}
          </dl>
          {!!result.errors?.length && (
            <div className="pt-2">
              <h3 className="text-sm font-medium text-gray-900">Erros</h3>
              <ul className="text-xs text-red-700 list-disc pl-5">
                {result.errors.map((er, idx) => (
                  <li key={idx}>
                    {er.line ? `Linha ${er.line}: ` : ''}{er.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <details className="pt-2">
            <summary className="text-xs text-blue-700 cursor-pointer">Ver JSON completo</summary>
            <pre className="text-xs bg-gray-50 border rounded p-2 whitespace-pre-wrap break-all">{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}
    </section>
  )
}
