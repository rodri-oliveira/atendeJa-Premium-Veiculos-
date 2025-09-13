import React from 'react'
import { useUIConfig } from '../config/provider'

export default function SettingsPage() {
  const cfg = useUIConfig()

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl md:text-2xl font-bold">Configurações (somente leitura)</h1>
        <p className="text-sm text-gray-600">Valores efetivos carregados de <code>config.json</code> em runtime, com fallback para defaults.</p>
      </header>

      <section className="bg-white border rounded p-4">
        <h2 className="font-semibold mb-2">Branding</h2>
        <dl className="text-sm grid grid-cols-1 md:grid-cols-2 gap-2">
          <div>
            <dt className="text-gray-500">App Title</dt>
            <dd>{cfg.branding?.appTitle || '—'}</dd>
          </div>
        </dl>
      </section>

      <section className="bg-white border rounded p-4">
        <h2 className="font-semibold mb-2">Kanban</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="text-sm font-medium mb-1">Colunas</h3>
            <ul className="text-sm list-disc pl-5 space-y-1">
              {cfg.kanban.columns.map((c, idx) => (
                <li key={idx}><code>{c.status}</code> — {c.title}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-medium mb-1">Ações por status</h3>
            <ul className="text-sm list-disc pl-5 space-y-1">
              {Object.entries(cfg.kanban.actions ?? {}).map(([status, actions]) => (
                <li key={status}>
                  <code>{status}</code>: {actions.map(a => a.label).join(', ') || '—'}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="bg-white border rounded p-4">
        <h2 className="font-semibold mb-2">JSON bruto</h2>
        <pre className="text-xs bg-gray-50 border rounded p-3 overflow-auto">
{JSON.stringify(cfg, null, 2)}
        </pre>
      </section>
    </div>
  )
}
