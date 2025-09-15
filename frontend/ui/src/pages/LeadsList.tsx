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

  useEffect(() => {
    let alive = true
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch('/api/re/leads', { cache: 'no-store' })
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
  }, [])

  return (
    <section className="space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Leads</h1>
        <div className="text-xs text-gray-500">Leads cadastrados</div>
      </header>
      {loading && <div className="text-sm text-gray-600">Carregando...</div>}
      {error && <div className="text-sm text-red-600">Erro: {error}</div>}
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
              {(data ?? []).map((l) => (
                <tr key={l.id} className="border-t">
                  <td className="px-3 py-2 text-gray-900">{l.id}</td>
                  <td className="px-3 py-2">{l.nome || '-'}</td>
                  <td className="px-3 py-2">{l.telefone || '-'}</td>
                  <td className="px-3 py-2">{l.email || '-'}</td>
                  <td className="px-3 py-2">{l.origem || '-'}</td>
                  <td className="px-3 py-2 text-xs text-gray-700">
                    {l.preferencias ? <code className="break-all">{JSON.stringify(l.preferencias)}</code> : '-'}
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
