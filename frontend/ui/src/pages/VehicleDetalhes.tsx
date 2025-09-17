import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { apiFetch } from '../lib/auth'

type MCPToolCall = { tool: string; params: Record<string, any>; result: any }

interface DetalhesVeiculo {
  id: number
  titulo: string
  marca?: string | null
  modelo?: string | null
  ano?: number | null
  categoria?: string | null
  preco?: number | null
  imagem?: string | null
  ativo?: boolean
}

export default function VehicleDetalhes() {
  const { id } = useParams<{ id: string }>()
  const [cpf, setCpf] = useState('00000000000')
  const [categoria, setCategoria] = useState<'USADO' | 'NOVO' | 'MOTOS'>('USADO')
  const [loading, setLoading] = useState(false) // pré-análise
  const [error, setError] = useState<string | null>(null) // pré-análise
  const [resumo, setResumo] = useState<string | null>(null)
  // detalhes do veículo
  const [veiculo, setVeiculo] = useState<DetalhesVeiculo | null>(null)
  const [loadingVeiculo, setLoadingVeiculo] = useState(true)
  const [errorVeiculo, setErrorVeiculo] = useState<string | null>(null)

  React.useEffect(() => {
    let alive = true
    async function load() {
      if (!id) return
      setLoadingVeiculo(true)
      setErrorVeiculo(null)
      try {
        const res = await fetch(`/api/veiculos/${encodeURIComponent(id)}`, { cache: 'no-store' })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const js = await res.json() as DetalhesVeiculo
        if (alive) setVeiculo(js)
      } catch (e: any) {
        if (alive) setErrorVeiculo(e?.message || 'erro')
      } finally {
        if (alive) setLoadingVeiculo(false)
      }
    }
    load()
    return () => { alive = false }
  }, [id])

  async function solicitarPreAnalise() {
    try {
      setLoading(true)
      setError(null)
      setResumo(null)
      const body = {
        input: '',
        mode: 'tool',
        tool: 'pan_pre_analise',
        params: { cpf: cpf.replace(/[^0-9]/g, ''), categoria },
        tenant_id: 'default',
      }
      const res = await apiFetch('/api/mcp/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const t = await res.text()
        throw new Error(`Erro ${res.status}${t ? ` - ${t}` : ''}`)
      }
      const data = await res.json() as { tool_calls?: MCPToolCall[] }
      const tc = Array.isArray(data.tool_calls) ? data.tool_calls[0] : null
      const result = tc?.result || {}
      const payload = result.data || {}
      const r = `Resultado (POC):\n` +
        `• CPF: ${payload.cpf || '***'}\n` +
        `• Categoria: ${payload.categoriaVeiculo || categoria}\n` +
        `• Status: ${payload.resultado || (result.ok ? 'OK' : 'ERRO')}\n` +
        `• Limite: R$ ${payload.limite_pre_aprovado ?? 0}`
      setResumo(r)
    } catch (e: any) {
      setError(e?.message || 'Erro inesperado')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="space-y-4">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <Link to="/veiculos" className="inline-flex items-center gap-1 text-primary-600 hover:underline focus:outline-none focus:ring-2 focus:ring-primary-300 rounded px-1">
            <span aria-hidden>←</span>
            <span>Voltar</span>
          </Link>
          <span className="text-slate-400">/</span>
          <span className="text-slate-800 font-medium">Detalhes do Veículo</span>
        </div>
      </header>
      {loadingVeiculo && <div className="text-sm text-gray-600">Carregando...</div>}
      {errorVeiculo && <div className="text-sm text-red-600">Erro: {errorVeiculo}</div>}
      {!loadingVeiculo && !errorVeiculo && veiculo && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-900">{veiculo.titulo}</h2>
                {veiculo.categoria && (
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">{veiculo.categoria}</span>
                )}
              </div>
              <div className="text-sm text-slate-600">{[veiculo.marca, veiculo.modelo, veiculo.ano].filter(Boolean).join(' · ')}</div>
              {typeof veiculo.preco === 'number' && (
                <div className="text-lg font-semibold text-primary-600">R$ {Math.round(veiculo.preco).toLocaleString('pt-BR')}</div>
              )}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-medium text-slate-900 mb-2">Imagem</h3>
            <div className="aspect-[4/3] overflow-hidden rounded-lg border border-slate-200 bg-slate-100 flex items-center justify-center">
              {veiculo.imagem ? (
                <img src={veiculo.imagem} alt={veiculo.titulo} className="w-full h-full object-cover" />
              ) : (
                <div className="text-slate-400">Sem imagem</div>
              )}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 space-y-3">
            <h2 className="font-semibold">Pré‑Análise (POC)</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <label className="text-sm">
                <div className="text-slate-600 mb-1">CPF</div>
                <input value={cpf} onChange={e => setCpf(e.target.value)} className="w-full px-3 py-2 border rounded" placeholder="00000000000" />
              </label>
              <label className="text-sm">
                <div className="text-slate-600 mb-1">Categoria</div>
                <select value={categoria} onChange={e => setCategoria(e.target.value as any)} className="w-full px-3 py-2 border rounded">
                  <option value="USADO">USADO</option>
                  <option value="NOVO">NOVO</option>
                  <option value="MOTOS">MOTOS</option>
                </select>
              </label>
            </div>
            <button onClick={solicitarPreAnalise} disabled={loading} className="px-3 py-2 rounded bg-primary-600 text-white hover:bg-primary-700 text-sm disabled:opacity-50">
              {loading ? 'Solicitando…' : 'Solicitar Pré‑Análise'}
            </button>
            {error && <div className="text-sm text-red-600">{error}</div>}
            {resumo && (
              <pre className="bg-slate-50 border rounded p-3 text-sm whitespace-pre-wrap">{resumo}</pre>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
