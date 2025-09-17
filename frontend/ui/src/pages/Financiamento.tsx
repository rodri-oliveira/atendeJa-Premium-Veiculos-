import React, { useState } from 'react'
import { apiFetch } from '../lib/auth'

export default function Financiamento() {
  const [cpf, setCpf] = useState('00000000000')
  const [categoria, setCategoria] = useState<'USADO' | 'NOVO' | 'MOTOS'>('USADO')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resumo, setResumo] = useState<string | null>(null)

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
      const data = await res.json() as { tool_calls?: Array<{ result: any }> }
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
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Análise de Financiamento</h1>
      <p className="text-slate-600">Digite o CPF e a categoria do veículo e execute a pré‑análise (modo POC).</p>
      <div className="bg-white rounded-lg shadow p-4 space-y-3 max-w-xl">
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
  )
}
