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
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold">Leads</h1>
          {!loading && !error && (
            <span className="inline-flex items-center px-2 py-0.5 text-xs rounded-full bg-gray-200 text-gray-800">
              {(data?.length ?? 0) === 1 ? '1 resultado' : `${data?.length ?? 0} resultados`}
            </span>
          )}
        </div>
        <div className="text-xs text-gray-500">Leads cadastrados</div>
      </header>
      {loading && <div className="text-sm text-gray-600">Carregando...</div>}
      {error && <div className="text-sm text-red-600">Erro: {error}</div>}
      {!loading && !error && (
        <div className="flex items-center justify-end text-xs text-gray-600">
          <div className="flex items-center gap-2">
            <button
              className="px-3 py-1.5 rounded border border-gray-300 bg-white disabled:opacity-50"
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
            >Anterior</button>
            <span>Página {Math.floor(offset / limit) + 1}</span>
            <button
              className="px-3 py-1.5 rounded border border-gray-300 bg-white disabled:opacity-50"
              onClick={() => setOffset(offset + limit)}
              disabled={(data?.length ?? 0) < limit}
            >Próxima</button>
          </div>
        </div>
      )}
      {!loading && !error && (
        <div className="overflow-auto rounded-lg border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-gray-600">
                <th className="px-3 py-2 font-medium">ID</th>
                <th className="px-3 py-2 font-medium">Nome</th>
                <th className="px-3 py-2 font-medium">Telefone</th>
                <th className="px-3 py-2 font-medium">Email</th>
                <th className="px-3 py-2 font-medium">Origem</th>
                <th className="px-3 py-2 font-medium">Preferências</th>
              </tr>
            </thead>
            <tbody>
              {(data ?? []).map((l, idx) => (
                <tr key={l.id} className="border-t odd:bg-gray-50">
                  <td className="px-3 py-2 text-gray-900">{l.id}</td>
                  <td className="px-3 py-2">{l.nome || '-'}</td>
                  <td className="px-3 py-2">{l.telefone || '-'}</td>
                  <td className="px-3 py-2">{l.email || '-'}</td>
                  <td className="px-3 py-2">{l.origem || '-'}</td>
                  <td className="px-3 py-2 text-xs text-gray-700">
                    {l.preferencias ? (
                      <div className="space-y-1">
                        <div className="flex flex-wrap gap-1">
                          {l.preferencias.finalidade && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                              {l.preferencias.finalidade === 'sale' ? 'Venda' : l.preferencias.finalidade === 'rent' ? 'Locação' : String(l.preferencias.finalidade)}
                            </span>
                          )}
                          {l.preferencias.cidade && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
                              {l.preferencias.cidade}
                            </span>
                          )}
                          {l.preferencias.tipo && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-gray-200 text-gray-800">
                              {l.preferencias.tipo === 'apartment' ? 'Apartamento' : l.preferencias.tipo === 'house' ? 'Casa' : String(l.preferencias.tipo)}
                            </span>
                          )}
                        </div>
                        <button
                          className="text-[11px] text-blue-700 underline"
                          onClick={() => setExpanded((s) => ({ ...s, [l.id]: !s[l.id] }))}
                        >
                          {expanded[l.id] ? 'Ocultar JSON' : 'Ver JSON'}
                        </button>
                        {expanded[l.id] && (
                          <pre className="max-w-xl whitespace-pre-wrap break-all bg-gray-50 border rounded p-2">{JSON.stringify(l.preferencias, null, 2)}</pre>
                        )}
                      </div>
                    ) : (
                      '-'
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
