import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch, isAuthenticated } from '../lib/auth'

interface ImportResult {
  processed?: number
  inserted?: number
  updated?: number
  errors?: Array<{ line?: number; message: string }>
  [k: string]: any
}

export default function ImportCsv() {
  const authed = isAuthenticated()

  // Leads
  const [fileLeads, setFileLeads] = useState<File | null>(null)
  const [loadingLeads, setLoadingLeads] = useState(false)
  const [errLeads, setErrLeads] = useState<string | null>(null)
  const [resLeads, setResLeads] = useState<ImportResult | null>(null)

  // Veículos
  const [fileVeic, setFileVeic] = useState<File | null>(null)
  const [loadingVeic, setLoadingVeic] = useState(false)
  const [errVeic, setErrVeic] = useState<string | null>(null)
  const [resVeic, setResVeic] = useState<ImportResult | null>(null)

  async function onImportLeads(e: React.FormEvent) {
    e.preventDefault()
    setErrLeads(null)
    setResLeads(null)
    if (!fileLeads) return setErrLeads('Selecione um arquivo CSV.')
    if (!authed) return setErrLeads('Faça login para enviar (use /login).')
    try {
      setLoadingLeads(true)
      const fd = new FormData()
      fd.append('file', fileLeads)
      const res = await apiFetch('/api/admin/leads/import-csv', { method: 'POST', body: fd })
      if (!res.ok) {
        if (res.status === 401) {
          setErrLeads('Sua sessão expirou ou você não está autenticado. Faça login novamente.');
          return
        }
        try {
          const js = await res.json()
          throw new Error(js?.detail || js?.message || `HTTP ${res.status}`)
        } catch {
          throw new Error(`HTTP ${res.status}`)
        }
      }
      const js = await res.json()
      setResLeads(js)
    } catch (e: any) {
      setErrLeads(e?.message || 'Falha no upload de leads')
    } finally {
      setLoadingLeads(false)
    }
  }

  async function onImportVeic(e: React.FormEvent) {
    e.preventDefault()
    setErrVeic(null)
    setResVeic(null)
    if (!fileVeic) return setErrVeic('Selecione um arquivo CSV.')
    if (!authed) return setErrVeic('Faça login para enviar (use /login).')
    try {
      setLoadingVeic(true)
      const fd = new FormData()
      fd.append('file', fileVeic)
      const res = await apiFetch('/api/admin/veiculos/import-csv', { method: 'POST', body: fd })
      if (!res.ok) {
        if (res.status === 401) {
          setErrVeic('Sua sessão expirou ou você não está autenticado. Faça login novamente.');
          return
        }
        try {
          const js = await res.json()
          throw new Error(js?.detail || js?.message || `HTTP ${res.status}`)
        } catch {
          throw new Error(`HTTP ${res.status}`)
        }
      }
      const js = await res.json()
      setResVeic(js)
    } catch (e: any) {
      setErrVeic(e?.message || 'Falha no upload de veículos')
    } finally {
      setLoadingVeic(false)
    }
  }

  return (
    <section className="space-y-8">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Importar CSV</h1>
        <div className="text-sm text-slate-500">Envie planilhas .csv para Leads e Veículos</div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Importar Leads */}
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Importar Leads</h2>
            <div className="text-xs text-slate-500">colunas: nome, telefone, email, origem</div>
          </div>
          {!authed && (
            <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
              Você precisa <Link to="/login" className="underline font-medium">entrar</Link> para importar CSV.
            </div>
          )}
          <form onSubmit={onImportLeads} className="space-y-3">
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => setFileLeads(e.target.files?.[0] || null)}
              className="text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 transition-colors"
            />
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={loadingLeads || !fileLeads}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingLeads ? 'Enviando...' : 'Enviar'}
              </button>
              <Link to="/leads" className="text-sm text-primary-700 hover:underline">Ver Leads →</Link>
            </div>
          </form>
          {errLeads && <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">{errLeads}</div>}
          {resLeads && (
            <details className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm">
              <summary className="cursor-pointer text-slate-700">Ver resultado</summary>
              <pre className="text-xs mt-2 whitespace-pre-wrap break-all">{JSON.stringify(resLeads, null, 2)}</pre>
            </details>
          )}
        </div>

        {/* Importar Veículos */}
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Importar Veículos</h2>
            <div className="text-xs text-slate-500">colunas: title, brand, model, year, category, price, image_url, active</div>
          </div>
          {!authed && (
            <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
              Você precisa <Link to="/login" className="underline font-medium">entrar</Link> para importar CSV.
            </div>
          )}
          <form onSubmit={onImportVeic} className="space-y-3">
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => setFileVeic(e.target.files?.[0] || null)}
              className="text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 transition-colors"
            />
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={loadingVeic || !fileVeic}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingVeic ? 'Enviando...' : 'Enviar'}
              </button>
              <Link to="/veiculos" className="text-sm text-primary-700 hover:underline">Ver Veículos →</Link>
            </div>
          </form>
          {errVeic && <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">{errVeic}</div>}
          {resVeic && (
            <details className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm">
              <summary className="cursor-pointer text-slate-700">Ver resultado</summary>
              <pre className="text-xs mt-2 whitespace-pre-wrap break-all">{JSON.stringify(resVeic, null, 2)}</pre>
            </details>
          )}
        </div>
      </div>

      <div className="text-sm text-slate-500">
        Dicas: arquivos de exemplo na pasta <code>docs/</code> deste projeto.
      </div>
    </section>
  )
}
