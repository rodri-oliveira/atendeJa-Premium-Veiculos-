import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

interface Imagem {
  id: number
  url: string
  is_capa: boolean
  ordem: number
}

interface Detalhes {
  id: number
  titulo: string
  descricao?: string | null
  tipo: 'apartment' | 'house' | string
  finalidade: 'sale' | 'rent' | string
  preco: number
  cidade: string
  estado: string
  bairro?: string | null
  dormitorios?: number | null
  banheiros?: number | null
  suites?: number | null
  vagas?: number | null
  area_total?: number | null
  area_util?: number | null
  imagens: Imagem[]
}

export default function ImovelDetalhes() {
  const { id } = useParams()
  const [data, setData] = useState<Detalhes | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    async function load() {
      if (!id) return
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/re/imoveis/${encodeURIComponent(id)}/detalhes`, { cache: 'no-store' })
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
  }, [id])

  return (
    <section className="space-y-4">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <Link to="/imoveis" className="inline-flex items-center gap-1 text-primary-600 hover:underline focus:outline-none focus:ring-2 focus:ring-primary-300 rounded px-1">
            <span aria-hidden>←</span>
            <span>Voltar</span>
          </Link>
          <span className="text-slate-400">/</span>
          <span className="text-slate-800 font-medium">Detalhes do Imóvel</span>
        </div>
      </header>
      {loading && <div className="text-sm text-gray-600">Carregando...</div>}
      {error && <div className="text-sm text-red-600">Erro: {error}</div>}
      {!loading && !error && data && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-900">{data.titulo}</h2>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                  {data.tipo === 'apartment' ? 'Apartamento' : data.tipo === 'house' ? 'Casa' : data.tipo}
                </span>
              </div>
              <div className="text-sm text-slate-600">
                {data.finalidade === 'sale' ? 'Venda' : 'Locação'} · {data.cidade}-{data.estado}
              </div>
              <div className="text-lg font-semibold text-primary-600">R$ {Math.round(data.preco).toLocaleString('pt-BR')}</div>
              {data.descricao && <p className="text-sm text-slate-700">{data.descricao}</p>}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-xs text-slate-700">
                {typeof data.dormitorios === 'number' && <div><span className="text-slate-500">Dormitórios:</span> {data.dormitorios}</div>}
                {typeof data.banheiros === 'number' && <div><span className="text-slate-500">Banheiros:</span> {data.banheiros}</div>}
                {typeof data.suites === 'number' && <div><span className="text-slate-500">Suítes:</span> {data.suites}</div>}
                {typeof data.vagas === 'number' && <div><span className="text-slate-500">Vagas:</span> {data.vagas}</div>}
                {typeof data.area_total === 'number' && <div><span className="text-slate-500">Área total:</span> {data.area_total} m²</div>}
                {typeof data.area_util === 'number' && <div><span className="text-slate-500">Área útil:</span> {data.area_util} m²</div>}
              </div>
            </div>
          </div>
          {!!data.imagens?.length && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-medium text-slate-900 mb-2">Galeria de imagens</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                {data.imagens.map((img) => (
                  <div key={img.id} className="aspect-[4/3] overflow-hidden rounded-lg border border-slate-200">
                    <img src={img.url} alt={`Imagem ${img.id}`} className="w-full h-full object-cover transition-transform duration-200 hover:scale-[1.02]" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
