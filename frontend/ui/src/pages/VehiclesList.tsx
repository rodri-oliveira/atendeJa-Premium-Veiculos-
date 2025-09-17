import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

type Vehicle = {
  id: number
  titulo: string
  marca?: string | null
  modelo?: string | null
  ano?: number | null
  categoria?: string | null
  preco?: number | null
  imagem?: string | null
}

export default function VehiclesList() {
  const [data, setData] = useState<Vehicle[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // filtros veículos
  const [categoria, setCategoria] = useState<string>('')
  const [marca, setMarca] = useState<string>('')
  const [precoMin, setPrecoMin] = useState<string>('')
  const [precoMax, setPrecoMax] = useState<string>('')
  // paginação
  const [limit] = useState<number>(12)
  const [offset, setOffset] = useState<number>(0)

  function clearFilters() {
    setCategoria('')
    setMarca('')
    setPrecoMin('')
    setPrecoMax('')
    setOffset(0)
  }

  // Ler filtros do querystring ao montar
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const c = params.get('categoria') || ''
    const m = params.get('marca') || ''
    const pmin = params.get('preco_min') || ''
    const pmax = params.get('preco_max') || ''
    const off = params.get('offset') || '0'
    if (c) setCategoria(c)
    if (m) setMarca(m)
    if (pmin) setPrecoMin(pmin)
    if (pmax) setPrecoMax(pmax)
    if (off) setOffset(Number(off) || 0)
  }, [])

  // Atualizar querystring quando filtros/offset mudarem
  useEffect(() => {
    const params = new URLSearchParams()
    if (categoria) params.set('categoria', categoria)
    if (marca) params.set('marca', marca)
    if (precoMin) params.set('preco_min', precoMin)
    if (precoMax) params.set('preco_max', precoMax)
    if (offset) params.set('offset', String(offset))
    const qs = params.toString()
    const newUrl = `${window.location.pathname}${qs ? `?${qs}` : ''}`
    if (newUrl !== window.location.pathname + window.location.search) {
      window.history.replaceState({}, '', newUrl)
    }
  }, [categoria, marca, precoMin, precoMax, offset])

  // Resetar offset ao mudar qualquer filtro
  useEffect(() => {
    setOffset(0)
  }, [categoria, marca, precoMin, precoMax])

  const queryString = useMemo(() => {
    const params = new URLSearchParams()
    if (categoria) params.set('categoria', categoria)
    if (marca) params.set('marca', marca)
    if (precoMin) params.set('preco_min', precoMin)
    if (precoMax) params.set('preco_max', precoMax)
    params.set('limit', String(limit))
    params.set('offset', String(offset))
    return params.toString()
  }, [categoria, marca, precoMin, precoMax, limit, offset])

  useEffect(() => {
    let alive = true
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const url = `/api/veiculos${queryString ? `?${queryString}` : ''}`
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
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">Veículos</h1>
            {!loading && !error && (
              <span className="inline-flex items-center px-3 py-1 text-sm font-medium rounded-full bg-primary-100 text-primary-800">
                {(data?.length ?? 0) === 1 ? '1 resultado' : `${data?.length ?? 0} resultados`}
              </span>
            )}
          </div>
          <div className="text-sm text-slate-500">Inventário</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <form className="grid grid-cols-2 sm:grid-cols-4 gap-3 items-end" onSubmit={(e) => e.preventDefault()}>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Categoria</label>
              <select value={categoria} onChange={(e) => setCategoria(e.target.value)} className="w-full rounded-lg border-slate-300 text-sm focus:ring-primary-500">
                <option value="">Todas</option>
                <option value="USADO">USADO</option>
                <option value="NOVO">NOVO</option>
                <option value="MOTOS">MOTOS</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Marca</label>
              <input value={marca} onChange={(e) => setMarca(e.target.value)} className="w-full rounded-lg border-slate-300 text-sm focus:ring-primary-500" placeholder="Ex.: Fiat" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Preço mín.</label>
              <input type="number" value={precoMin} onChange={(e) => setPrecoMin(e.target.value)} className="w-full rounded-lg border-slate-300 text-sm focus:ring-primary-500" placeholder="0" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Preço máx.</label>
              <input type="number" value={precoMax} onChange={(e) => setPrecoMax(e.target.value)} className="w-full rounded-lg border-slate-300 text-sm focus:ring-primary-500" placeholder="" />
            </div>
            <div className="sm:col-span-4 flex justify-end">
              <button type="button" onClick={clearFilters} className="px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 transition-all">Limpar filtros</button>
            </div>
          </form>
        </div>
      </header>
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
              {/* Skeleton para imagem */}
              <div className="h-48 skeleton"></div>
              
              <div className="p-5 space-y-4">
                {/* Skeleton para título */}
                <div className="space-y-2">
                  <div className="h-5 skeleton rounded w-3/4"></div>
                  <div className="h-4 skeleton rounded w-1/2"></div>
                </div>
                
                {/* Skeleton para preço */}
                <div className="flex items-center justify-between">
                  <div className="h-7 skeleton rounded w-24"></div>
                  <div className="h-4 skeleton rounded w-16"></div>
                </div>
                
                {/* Skeleton para botão */}
                <div className="h-10 skeleton rounded"></div>
              </div>
            </div>
          ))}
        </div>
      )}
      {error && <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-4">Erro: {error}</div>}
      {!loading && !error && (data?.length ?? 0) === 0 && (
        <div className="text-center py-12">
          <div className="text-slate-400 text-lg mb-2">Nenhum veículo encontrado</div>
          <div className="text-sm text-slate-500">Ajuste os filtros acima e tente novamente.</div>
        </div>
      )}
      {!loading && !error && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {(data ?? []).map((v) => (
            <article key={v.id} className="group rounded-xl border border-slate-200 bg-white shadow-card hover:shadow-hover transition-all overflow-hidden">
              <Link to={`/veiculos/${v.id}`}>
                <div className="h-48 bg-slate-100 relative">
                  {v.imagem ? (
                    <img src={v.imagem} alt={v.titulo} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-slate-400">Sem imagem</div>
                  )}
                  {v.categoria && (
                    <span className="absolute top-2 left-2 px-2 py-1 rounded-full text-xs font-medium bg-white/90 text-slate-700">{v.categoria}</span>
                  )}
                </div>
                <div className="p-4 space-y-2">
                  <h2 className="text-lg font-semibold text-slate-900 group-hover:text-primary-600 transition-colors">{v.titulo}</h2>
                  <div className="text-sm text-slate-600">{[v.marca, v.modelo, v.ano].filter(Boolean).join(' · ')}</div>
                  <div className="text-2xl font-bold text-primary-600">{typeof v.preco === 'number' ? `R$ ${Math.round(v.preco).toLocaleString('pt-BR')}` : '-'}</div>
                </div>
              </Link>
            </article>
          ))}
        </div>
      )}
      {!loading && !error && (
        <div className="flex items-center justify-between pt-6">
          <button
            className="flex items-center px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
          >
            ← Anterior
          </button>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600">Página</span>
            <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-lg font-medium">
              {Math.floor(offset / limit) + 1}
            </span>
          </div>
          <button
            className="flex items-center px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            onClick={() => setOffset(offset + limit)}
            disabled={(data?.length ?? 0) < limit}
          >
            Próxima →
          </button>
        </div>
      )}
    </section>
  )
}
