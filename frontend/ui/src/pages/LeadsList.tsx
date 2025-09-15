import React, { useEffect, useState } from 'react'

interface Lead {
  id: number
  nome?: string | null
  telefone?: string | null
  email?: string | null
  origem?: string | null
  preferencias?: Record<string, any> | null
}

export default function LeadsList() {
  const [data, setData] = useState<Lead[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})
  const [limit] = useState<number>(20)
  const [offset, setOffset] = useState<number>(0)

  // Ler offset do querystring ao montar
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const off = Number(params.get('offset') || '0')
    if (!Number.isNaN(off) && off > 0) setOffset(off)
  }, [])

  useEffect(() => {
    let alive = true
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const url = `/api/re/leads?limit=${limit}&offset=${offset}`
        const res = await fetch(url, { cache: 'no-store' })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const js = await res.json()
        if (alive) setData(js)
      } catch (e: any) {
        if (alive) setError(e?.message || 'erro')
      } finally {
        if (alive) setLoading(false)
      }
    }
    load()
    return () => { alive = false }
  }, [limit, offset])

  // Atualizar querystring quando offset mudar
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (offset) params.set('offset', String(offset))
    else params.delete('offset')
    const qs = params.toString()
    const newUrl = `${window.location.pathname}${qs ? `?${qs}` : ''}`
    if (newUrl !== window.location.pathname + window.location.search) {
      window.history.replaceState({}, '', newUrl)
    }
  }, [offset])

  return (
    <section className="space-y-4">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-slate-800">Leads</h1>
          {!loading && !error && (
            <span className="inline-flex items-center px-3 py-1 text-sm font-medium rounded-full bg-primary-100 text-primary-800">
              {(data?.length ?? 0) === 1 ? '1 resultado' : `${data?.length ?? 0} resultados`}
            </span>
          )}
        </div>
        <div className="text-sm text-slate-500">Leads cadastrados</div>
      </header>
      {loading && (
        <div className="overflow-auto rounded-xl border border-slate-200 bg-white shadow-card">
          <table className="min-w-full">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">ID</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Nome</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Telefone</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Email</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Origem</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Preferências</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td className="px-6 py-4"><div className="h-4 skeleton rounded w-8"></div></td>
                  <td className="px-6 py-4"><div className="h-4 skeleton rounded w-24"></div></td>
                  <td className="px-6 py-4"><div className="h-4 skeleton rounded w-32"></div></td>
                  <td className="px-6 py-4"><div className="h-4 skeleton rounded w-40"></div></td>
                  <td className="px-6 py-4"><div className="h-4 skeleton rounded w-20"></div></td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <div className="h-6 skeleton rounded-full w-16"></div>
                      <div className="h-6 skeleton rounded-full w-20"></div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {error && <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-4">Erro: {error}</div>}
      {!loading && !error && (
        <div className="flex items-center justify-end">
          <div className="flex items-center gap-3">
            <button
              className="px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
            >← Anterior</button>
            <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-lg font-medium text-sm">
              Página {Math.floor(offset / limit) + 1}
            </span>
            <button
              className="px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              onClick={() => setOffset(offset + limit)}
              disabled={(data?.length ?? 0) < limit}
            >Próxima →</button>
          </div>
        </div>
      )}
      {!loading && !error && (
        <div className="overflow-auto rounded-xl border border-slate-200 bg-white shadow-card">
          <table className="min-w-full">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">ID</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Nome</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Telefone</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Email</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Origem</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Preferências</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {(data ?? []).map((l, idx) => (
                <tr key={l.id} className="hover:bg-slate-50 transition-colors duration-200 table-row">
                  <td className="px-6 py-4 text-sm font-medium text-slate-900">{l.id}</td>
                  <td className="px-6 py-4 text-sm text-slate-900">{l.nome || <span className="text-slate-400 italic">Não informado</span>}</td>
                  <td className="px-6 py-4 text-sm text-slate-600">{l.telefone || <span className="text-slate-400 italic">Não informado</span>}</td>
                  <td className="px-6 py-4 text-sm text-slate-600">{l.email || <span className="text-slate-400 italic">Não informado</span>}</td>
                  <td className="px-6 py-4 text-sm text-slate-600">{l.origem || <span className="text-slate-400 italic">Não informado</span>}</td>
                  <td className="px-6 py-4 text-sm">
                    {l.preferencias ? (
                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-2">
                          {l.preferencias.finalidade && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                              {l.preferencias.finalidade === 'sale' ? 'Venda' : l.preferencias.finalidade === 'rent' ? 'Locação' : String(l.preferencias.finalidade)}
                            </span>
                          )}
                          {l.preferencias.cidade && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                              {l.preferencias.cidade}
                            </span>
                          )}
                          {l.preferencias.tipo && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                              {l.preferencias.tipo === 'apartment' ? 'Apartamento' : l.preferencias.tipo === 'house' ? 'Casa' : String(l.preferencias.tipo)}
                            </span>
                          )}
                        </div>
                        <button
                          className="text-xs text-primary-600 hover:text-primary-700 font-medium transition-colors"
                          onClick={() => setExpanded((s) => ({ ...s, [l.id]: !s[l.id] }))}
                        >
                          {expanded[l.id] ? 'Ocultar JSON' : 'Ver JSON'}
                        </button>
                        {expanded[l.id] && (
                          <pre className="max-w-xl whitespace-pre-wrap break-all bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-700">{JSON.stringify(l.preferencias, null, 2)}</pre>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
