import React, { useEffect, useMemo, useState } from 'react'
import { apiFetch, isAuthenticated } from '../lib/auth'
import { Link, useNavigate } from 'react-router-dom'

type Role = 'admin' | 'collaborator'

type User = {
  id: number
  email: string
  full_name?: string | null
  role: Role
  is_active: boolean
}

export default function UsersAdmin() {
  const [list, setList] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState<Role>('collaborator')
  const [creating, setCreating] = useState(false)
  const [filterRole, setFilterRole] = useState<string>('')
  const [filterActive, setFilterActive] = useState<string>('')
  const authed = isAuthenticated()
  const navigate = useNavigate()

  useEffect(() => {
    if (!authed) navigate('/login')
  }, [authed])

  const queryString = useMemo(() => {
    const p = new URLSearchParams()
    if (filterRole) p.set('role', filterRole)
    if (filterActive) p.set('is_active', filterActive)
    return p.toString()
  }, [filterRole, filterActive])

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch(`/api/admin/users${queryString ? `?${queryString}` : ''}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const js = await res.json()
      setList(js)
    } catch (e: any) {
      setError(e?.message || 'erro')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [queryString])

  async function onCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    setError(null)
    try {
      const payload = { email, password, full_name: fullName || undefined, role, is_active: true }
      const res = await apiFetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        let msg = `HTTP ${res.status}`
        try { const js = await res.json(); msg = js?.detail || js?.message || msg } catch {}
        throw new Error(msg)
      }
      setEmail(''); setPassword(''); setFullName(''); setRole('collaborator')
      await load()
    } catch (e: any) {
      setError(e?.message || 'falha ao criar usuário')
    } finally {
      setCreating(false)
    }
  }

  async function onToggleActive(u: User) {
    try {
      const res = await apiFetch(`/api/admin/users/${u.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !u.is_active }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await load()
    } catch (e) {
      console.warn(e)
    }
  }

  async function onPromote(u: User) {
    try {
      const res = await apiFetch(`/api/admin/users/${u.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: u.role === 'admin' ? 'collaborator' : 'admin' }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await load()
    } catch (e) {
      console.warn(e)
    }
  }

  return (
    <section className="space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Usuários</h1>
        <div className="text-sm text-slate-500">Gestão de usuários e perfis</div>
      </header>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <form onSubmit={onCreate} className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
            <input className="w-full rounded-lg border-slate-300 text-sm" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Senha</label>
            <input className="w-full rounded-lg border-slate-300 text-sm" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Nome</label>
            <input className="w-full rounded-lg border-slate-300 text-sm" type="text" value={fullName} onChange={e => setFullName(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Papel</label>
            <select className="w-full rounded-lg border-slate-300 text-sm" value={role} onChange={e => setRole(e.target.value as Role)}>
              <option value="collaborator">Colaborador</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <button disabled={creating} className="px-4 py-2 text-sm font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700">{creating ? 'Criando...' : 'Criar'}</button>
            <Link className="text-sm text-slate-600 underline" to="/imoveis">Voltar</Link>
          </div>
        </form>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Filtrar papel</label>
            <select className="w-full rounded-lg border-slate-300 text-sm" value={filterRole} onChange={e => setFilterRole(e.target.value)}>
              <option value="">Todos</option>
              <option value="admin">Admin</option>
              <option value="collaborator">Colaborador</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Ativo</label>
            <select className="w-full rounded-lg border-slate-300 text-sm" value={filterActive} onChange={e => setFilterActive(e.target.value)}>
              <option value="">Todos</option>
              <option value="true">Ativos</option>
              <option value="false">Inativos</option>
            </select>
          </div>
        </div>

        {loading && <div className="text-sm text-slate-500">Carregando...</div>}
        {error && <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">{error}</div>}

        {!loading && !error && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-600">
                  <th className="py-2 pr-3">ID</th>
                  <th className="py-2 pr-3">Email</th>
                  <th className="py-2 pr-3">Nome</th>
                  <th className="py-2 pr-3">Papel</th>
                  <th className="py-2 pr-3">Ativo</th>
                  <th className="py-2 pr-3">Ações</th>
                </tr>
              </thead>
              <tbody>
                {list.map(u => (
                  <tr key={u.id} className="border-t border-slate-200">
                    <td className="py-2 pr-3">{u.id}</td>
                    <td className="py-2 pr-3">{u.email}</td>
                    <td className="py-2 pr-3">{u.full_name || '-'}</td>
                    <td className="py-2 pr-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${u.role === 'admin' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-800'}`}>{u.role}</span>
                    </td>
                    <td className="py-2 pr-3">{u.is_active ? 'Sim' : 'Não'}</td>
                    <td className="py-2 pr-3 flex gap-2">
                      <button onClick={() => onPromote(u)} className="px-3 py-1 rounded bg-indigo-600 text-white">{u.role === 'admin' ? 'Rebaixar' : 'Promover'}</button>
                      <button onClick={() => onToggleActive(u)} className={`px-3 py-1 rounded ${u.is_active ? 'bg-amber-600 text-white' : 'bg-emerald-600 text-white'}`}>{u.is_active ? 'Desativar' : 'Ativar'}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}
