import React, { useEffect, useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { apiFetch } from '../lib/auth'

type MetricsResponse = {
  generated_at: string
  labels: string[]
  leads_por_mes: number[]
  conversas_whatsapp: number[]
  taxa_conversao: number[]
}

export default function Reports() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [periodMonths, setPeriodMonths] = useState<number>(6)
  const [channel, setChannel] = useState<string>('whatsapp')
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')

  useEffect(() => {
    let alive = true
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const qp = new URLSearchParams()
        if (startDate && endDate) {
          qp.set('start_date', startDate)
          qp.set('end_date', endDate)
        } else {
          qp.set('period_months', String(periodMonths))
        }
        if (channel) qp.set('channel', channel)
        const res = await apiFetch(`/api/metrics/overview?${qp.toString()}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const js = await res.json()
        if (alive) setMetrics(js)
      } catch (e: any) {
        if (alive) setError(e?.message || 'Falha ao carregar métricas')
      } finally {
        if (alive) setLoading(false)
      }
    }
    load()
    return () => { alive = false }
  }, [periodMonths, channel, startDate, endDate])

  const meses = metrics?.labels || ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']

  const leadsOption = useMemo(() => ({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: meses },
    yAxis: { type: 'value' },
    series: [{
      name: 'Leads', type: 'bar', data: metrics?.leads_por_mes ?? [12, 18, 25, 22, 30, 28],
      itemStyle: { color: '#2563eb' }
    }]
  }), [metrics, meses])

  const whatsOption = useMemo(() => ({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: meses },
    yAxis: { type: 'value' },
    series: [{ name: 'Conversas WhatsApp', type: 'line', data: metrics?.conversas_whatsapp ?? [80, 110, 95, 120, 130, 140], smooth: true, lineStyle: { width: 3, color: '#16a34a' } }]
  }), [metrics, meses])

  const convOption = useMemo(() => ({
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].axisValue}: ${p[0].data}%` },
    xAxis: { type: 'category', data: meses },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [{ name: 'Conversão', type: 'line', data: metrics?.taxa_conversao ?? [8, 9, 11, 10, 12, 13], areaStyle: {}, itemStyle: { color: '#9333ea' } }]
  }), [metrics, meses])

  return (
    <section className="space-y-5">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Relatórios</h1>
        <div className="text-sm text-slate-500">Indicadores operacionais e de marketing</div>
      </header>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm grid grid-cols-1 md:grid-cols-4 gap-3">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Período</label>
          <select
            className="w-full rounded-lg border-slate-300 text-sm"
            value={periodMonths}
            onChange={e => setPeriodMonths(Number(e.target.value))}
          >
            <option value={6}>Últimos 6 meses</option>
            <option value={12}>Últimos 12 meses</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Canal</label>
          <select
            className="w-full rounded-lg border-slate-300 text-sm"
            value={channel}
            onChange={e => setChannel(e.target.value)}
          >
            <option value="whatsapp">WhatsApp</option>
            <option value="all">Todos</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Data inicial</label>
          <input
            type="date"
            className="w-full rounded-lg border-slate-300 text-sm"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
            max={endDate || undefined}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Data final</label>
          <input
            type="date"
            className="w-full rounded-lg border-slate-300 text-sm"
            value={endDate}
            onChange={e => setEndDate(e.target.value)}
            min={startDate || undefined}
          />
        </div>
        <div className="md:col-span-4 flex items-center gap-2 pt-1">
          <button
            onClick={() => { setStartDate(''); setEndDate(''); }}
            disabled={loading || (!startDate && !endDate)}
            className="px-3 py-2 text-sm font-medium rounded-lg bg-slate-200 text-slate-800 hover:bg-slate-300 disabled:opacity-50"
          >
            Limpar datas
          </button>
          <div className="text-xs text-slate-500">
            {startDate && endDate ? `Período: ${startDate} a ${endDate}` : `Período rápido: ${periodMonths} meses`}
          </div>
        </div>
      </div>

      {loading && <div className="text-sm text-slate-500">Carregando dados...</div>}
      {error && <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">{error}</div>}

      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="text-sm font-medium text-slate-700 mb-2">Leads por mês</div>
            <ReactECharts option={leadsOption} style={{ height: 280 }} notMerge={true} lazyUpdate={true} />
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="text-sm font-medium text-slate-700 mb-2">Conversas WhatsApp</div>
            <ReactECharts option={whatsOption} style={{ height: 280 }} notMerge={true} lazyUpdate={true} />
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm lg:col-span-2">
            <div className="text-sm font-medium text-slate-700 mb-2">Taxa de conversão (%)</div>
            <ReactECharts option={convOption} style={{ height: 320 }} notMerge={true} lazyUpdate={true} />
          </div>
        </div>
      )}
    </section>
  )
}
