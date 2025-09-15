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

  function clearFilters() {
    setFinalidade('')
    setTipo('')
    setCidade('')
    setEstado('')
    setPrecoMin('')
    setPrecoMax('')
    setDormMin('')
    setOffset(0)
  }

  // Ler filtros do querystring ao montar
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const f = params.get('finalidade') || ''
    const t = params.get('tipo') || ''
    const c = params.get('cidade') || ''
    const e = params.get('estado') || ''
    const pmin = params.get('preco_min') || ''
    const pmax = params.get('preco_max') || ''
    const dmin = params.get('dormitorios_min') || ''
    const off = params.get('offset') || '0'
    if (f) setFinalidade(f)
    if (t) setTipo(t)
    if (c) setCidade(c)
    if (e) setEstado(e)
    if (pmin) setPrecoMin(pmin)
    if (pmax) setPrecoMax(pmax)
    if (dmin) setDormMin(dmin)
    if (off) setOffset(Number(off) || 0)
  }, [])

  // Atualizar querystring quando filtros/offset mudarem
  useEffect(() => {
    const params = new URLSearchParams()
    if (finalidade) params.set('finalidade', finalidade)
    if (tipo) params.set('tipo', tipo)
    if (cidade) params.set('cidade', cidade)
    if (estado) params.set('estado', estado)
    if (precoMin) params.set('preco_min', precoMin)
    if (precoMax) params.set('preco_max', precoMax)
    if (dormMin) params.set('dormitorios_min', dormMin)
    if (offset) params.set('offset', String(offset))
    const qs = params.toString()
    const newUrl = `${window.location.pathname}${qs ? `?${qs}` : ''}`
    if (newUrl !== window.location.pathname + window.location.search) {
      window.history.replaceState({}, '', newUrl)
    }
  }, [finalidade, tipo, cidade, estado, precoMin, precoMax, dormMin, offset])

  // Resetar offset ao mudar qualquer filtro
  useEffect(() => {
    setOffset(0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [finalidade, tipo, cidade, estado, precoMin, precoMax, dormMin])

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
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-slate-800">Imóveis</h1>
            {!loading && !error && (
              <span className="inline-flex items-center px-3 py-1 text-sm font-medium rounded-full bg-primary-100 text-primary-800">
                {(data?.length ?? 0) === 1 ? '1 resultado' : `${data?.length ?? 0} resultados`}
              </span>
            )}
          </div>
          <div className="text-sm text-slate-500">Lista dos imóveis ativos</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <form className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 items-end" onSubmit={(e) => e.preventDefault()}>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Finalidade</label>
              <select value={finalidade} onChange={e => setFinalidade(e.target.value)} className="w-full rounded-lg border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors">
                <option value="">Todas</option>
                <option value="sale">Venda</option>
                <option value="rent">Locação</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Tipo</label>
              <select value={tipo} onChange={e => setTipo(e.target.value)} className="w-full rounded-lg border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors">
                <option value="">Todos</option>
                <option value="apartment">Apartamento</option>
                <option value="house">Casa</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Cidade</label>
              <input value={cidade} onChange={e => setCidade(e.target.value)} className="w-full rounded-lg border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors" placeholder="Ex.: São Paulo" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Estado (UF)</label>
              <input value={estado} onChange={e => setEstado(e.target.value.toUpperCase())} className="w-full rounded-lg border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors" placeholder="SP" maxLength={2} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Preço mín.</label>
              <input type="number" value={precoMin} onChange={e => setPrecoMin(e.target.value)} className="w-full rounded-lg border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors" placeholder="0" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Preço máx.</label>
              <input type="number" value={precoMax} onChange={e => setPrecoMax(e.target.value)} className="w-full rounded-lg border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors" placeholder="" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Dormitórios mín.</label>
              <input type="number" value={dormMin} onChange={e => setDormMin(e.target.value)} className="w-full rounded-lg border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors" placeholder="" />
            </div>
            <div className="lg:col-span-4" />
            <div className="flex justify-end">
              <button type="button" onClick={clearFilters} className="px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-400 transition-all duration-200">
                Limpar filtros
              </button>
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
          <div className="text-slate-400 text-lg mb-2">Nenhum imóvel encontrado</div>
          <div className="text-sm text-slate-500">Ajuste os filtros acima e tente novamente.</div>
        </div>
      )}
      {!loading && !error && (
        <div className="flex items-center justify-end text-xs text-gray-600">
          <div>Página {Math.floor(offset / limit) + 1}</div>
        </div>
      )}
      {!loading && !error && (data?.length ?? 0) > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {(data ?? []).map((p, index) => (
            <article 
              key={p.id} 
              className="group rounded-xl border border-slate-200 bg-white shadow-card hover:shadow-hover transition-all duration-300 overflow-hidden hover-lift card-entrance"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {/* Simulação de imagem */}
              <div className="h-48 bg-gradient-to-br from-slate-100 to-slate-200 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
                <div className="absolute top-3 left-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    p.finalidade === 'sale' 
                      ? 'bg-emerald-100 text-emerald-800' 
                      : 'bg-amber-100 text-amber-800'
                  }`}>
                    {p.finalidade === 'sale' ? 'Venda' : 'Locação'}
                  </span>
                </div>
                <div className="absolute top-3 right-3">
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-white/90 text-slate-700">
                    {p.tipo === 'apartment' ? 'Apartamento' : p.tipo === 'house' ? 'Casa' : p.tipo}
                  </span>
                </div>
              </div>
              
              <div className="p-5 space-y-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900 group-hover:text-primary-600 transition-colors duration-200 line-clamp-2">
                    {p.titulo}
                  </h2>
                  <div className="text-sm text-slate-500 mt-1">
                    {p.cidade}-{p.estado}
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="text-2xl font-bold text-primary-600">
                    R$ {Math.round(p.preco).toLocaleString('pt-BR')}
                  </div>
                  {typeof p.dormitorios === 'number' && (
                    <div className="text-sm text-slate-500">
                      {p.dormitorios} dorm.
                    </div>
                  )}
                </div>
                
                <div className="pt-2">
                  <Link 
                    to={`/imoveis/${p.id}`} 
                    className="block w-full text-center px-4 py-2.5 text-sm font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-all duration-200 hover-lift"
                  >
                    Ver Detalhes
                  </Link>
                </div>
              </div>
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
