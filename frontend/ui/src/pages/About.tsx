import React, { useEffect, useState } from 'react'

interface OpsConfig {
  app_env: string
  wa_provider: string
  default_tenant: string
  re_read_only: boolean
  version: string
}

export default function About() {
  const [cfg, setCfg] = useState<OpsConfig | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const r = await fetch('/api/ops/config', { cache: 'no-store' })
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const js = await r.json()
        if (alive) setCfg(js)
      } catch (e: any) {
        if (alive) setErr(e?.message || 'erro')
      }
    })()
    return () => { alive = false }
  }, [])

  const frontendVersion = '0.1.0'

  return (
    <section className="space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Sobre / Docs</h1>
        <div className="text-xs text-gray-500">AtendeJá — ND Imóveis</div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-medium text-gray-900 mb-2">Links úteis</h2>
          <ul className="list-disc pl-5 text-sm text-blue-800 space-y-1">
            <li><a className="underline" href="/api/ops/config" target="_blank" rel="noreferrer">GET /ops/config</a></li>
            <li><a className="underline" href="/api/ops/ping/meta" target="_blank" rel="noreferrer">GET /ops/ping/meta</a></li>
          </ul>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-medium text-gray-900 mb-2">Versões</h2>
          <dl className="text-sm text-gray-700 space-y-1">
            <div className="flex justify-between"><dt>Frontend</dt><dd className="font-mono">{frontendVersion}</dd></div>
            <div className="flex justify-between"><dt>Backend</dt><dd className="font-mono">{cfg?.version || '-'}</dd></div>
          </dl>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-medium text-gray-900 mb-2">Dicas rápidas</h2>
        <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
          <li>Importar CSV de Imóveis em <span className="font-mono">Imobiliário &gt; Importar CSV</span>. Após enviar, clique em "Ver imóveis".</li>
          <li>Filtros de <span className="font-mono">Imóveis</span> ficam persistidos na URL (querystring). Compartilhe a URL para manter contexto.</li>
          <li>Leads possuem paginação com offset persistido no querystring.</li>
        </ul>
        {err && <div className="mt-2 text-xs text-red-700">Erro ao consultar /ops/config: {err}</div>}
      </div>
    </section>
  )
}
