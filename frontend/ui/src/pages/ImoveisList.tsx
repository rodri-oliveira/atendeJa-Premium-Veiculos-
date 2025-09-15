import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

interface Imovel {
  id: number
  titulo: string
  tipo: 'apartment' | 'house' | string
  finalidade: 'sale' | 'rent' | string
  preco: number
  cidade: string
  estado: string
  bairro?: string | null
  dormitorios?: number | null
  ativo: boolean
}

export default function ImoveisList() {
  const [data, setData] = useState<Imovel[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // filtros
  const [finalidade, setFinalidade] = useState<string>('')
  const [tipo, setTipo] = useState<string>('')
  const [cidade, setCidade] = useState<string>('')
  const [estado, setEstado] = useState<string>('')
  const [precoMin, setPrecoMin] = useState<string>('')
  const [precoMax, setPrecoMax] = useState<string>('')
  const [dormMin, setDormMin] = useState<string>('')
  // paginação
  const [limit] = useState<number>(12)
  const [offset, setOffset] = useState<number>(0)

  const queryString = useMemo(() => {
    const params = new URLSearchParams()
    if (finalidade) params.set('finalidade', finalidade)
    if (tipo) params.set('tipo', tipo)
    if (cidade) params.set('cidade', cidade)
    if (estado) params.set('estado', estado)
    if (precoMin) params.set('preco_min', precoMin)
    if (precoMax) params.set('preco_max', precoMax)
    if (dormMin) params.set('dormitorios_min', dormMin)
    params.set('limit', String(limit))
    params.set('offset', String(offset))
    return params.toString()
  }, [finalidade, tipo, cidade, estado, precoMin, precoMax, dormMin, limit, offset])

  useEffect(() => {
    let alive = true
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const url = `/api/re/imoveis${queryString ? `?${queryString}` : ''}`
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
  }, [queryString])

  return (
    <section className="space-y-4">
      <header className="space-y-3">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Imóveis</h1>
          <div className="text-xs text-gray-500">Lista dos imóveis ativos</div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-3">
          <form className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 items-end" onSubmit={(e) => e.preventDefault()}>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Finalidade</label>
              <select value={finalidade} onChange={e => setFinalidade(e.target.value)} className="w-full rounded border-gray-300 text-sm">
                <option value="">Todas</option>
                <option value="sale">Venda</option>
                <option value="rent">Locação</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Tipo</label>
              <select value={tipo} onChange={e => setTipo(e.target.value)} className="w-full rounded border-gray-300 text-sm">
                <option value="">Todos</option>
                <option value="apartment">Apartamento</option>
                <option value="house">Casa</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Cidade</label>
              <input value={cidade} onChange={e => setCidade(e.target.value)} className="w-full rounded border-gray-300 text-sm" placeholder="Ex.: São Paulo" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Estado (UF)</label>
              <input value={estado} onChange={e => setEstado(e.target.value.toUpperCase())} className="w-full rounded border-gray-300 text-sm" placeholder="SP" maxLength={2} />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Preço mín.</label>
              <input type="number" value={precoMin} onChange={e => setPrecoMin(e.target.value)} className="w-full rounded border-gray-300 text-sm" placeholder="0" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Preço máx.</label>
              <input type="number" value={precoMax} onChange={e => setPrecoMax(e.target.value)} className="w-full rounded border-gray-300 text-sm" placeholder="" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Dormitórios mín.</label>
              <input type="number" value={dormMin} onChange={e => setDormMin(e.target.value)} className="w-full rounded border-gray-300 text-sm" placeholder="" />
            </div>
            <div className="lg:col-span-5" />
          </form>
        </div>
      </header>
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-gray-200 bg-white shadow-sm p-4 animate-pulse h-40" />
          ))}
        </div>
      )}
      {error && <div className="text-sm text-red-600">Erro: {error}</div>}
      {!loading && !error && (data?.length ?? 0) === 0 && (
        <div className="text-sm text-gray-600">Nenhum imóvel encontrado com os filtros atuais.</div>
      )}
      {!loading && !error && (data?.length ?? 0) > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {(data ?? []).map((p) => (
            <article key={p.id} className="rounded-lg border border-gray-200 bg-white shadow-sm hover:shadow transition">
              <div className="p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-medium text-gray-900">{p.titulo}</h2>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                    {p.tipo === 'apartment' ? 'Apartamento' : p.tipo === 'house' ? 'Casa' : p.tipo}
                  </span>
                </div>
                <div className="text-xs text-gray-600">
                  {p.finalidade === 'sale' ? 'Venda' : 'Locação'} · {p.cidade}-{p.estado}
                </div>
                <div className="text-base font-semibold text-emerald-700">R$ {Math.round(p.preco).toLocaleString('pt-BR')}</div>
                {typeof p.dormitorios === 'number' && (
                  <div className="text-xs text-gray-500">Dormitórios: {p.dormitorios}</div>
                )}
                <div className="pt-2">
                  <Link to={`/imoveis/${p.id}`} className="inline-flex items-center px-3 py-1.5 text-sm rounded bg-gray-900 text-white hover:bg-gray-800">
                    Detalhes
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
      {!loading && !error && (
        <div className="flex items-center justify-between pt-2">
          <button
            className="px-3 py-1.5 text-sm rounded border border-gray-300 bg-white disabled:opacity-50"
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
          >
            Anterior
          </button>
          <div className="text-xs text-gray-600">Página {Math.floor(offset / limit) + 1}</div>
          <button
            className="px-3 py-1.5 text-sm rounded border border-gray-300 bg-white disabled:opacity-50"
            onClick={() => setOffset(offset + limit)}
            disabled={(data?.length ?? 0) < limit}
          >
            Próxima
          </button>
        </div>
      )}
    </section>
  )
}
