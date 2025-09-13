import React from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate, useSearchParams, Link } from 'react-router-dom'
import AppShell from './layouts/AppShell'
import KanbanPage from './pages/KanbanPage'
import SettingsPage from './pages/SettingsPage'
import DeliveryPage from './pages/DeliveryPage'
import { AuthProvider, useAuth } from './auth/provider'

function Placeholder({ title }: { title: string }) {
  return <div className="text-sm text-gray-700">{title} — em breve</div>
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<AppShell />}> 
            <Route index element={<Navigate to="/orders" replace />} />
            <Route path="dashboard" element={<Placeholder title="Dashboard" />} />
            <Route path="orders" element={<KanbanPage />} />
            <Route path="delivery" element={<DeliveryPage />} />
            <Route path="menu" element={<Placeholder title="Cardápio" />} />
            <Route path="customers" element={<Placeholder title="Clientes" />} />
            <Route path="settings" element={<RequireManager><SettingsPage /></RequireManager>} />
            <Route path="login" element={<LoginPage />} />
            <Route path="*" element={<Navigate to="/orders" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

function RequireManager({ children }: { children: React.ReactNode }) {
  const { auth } = useAuth()
  const loc = useLocation()
  if (auth.role !== 'manager') {
    const from = encodeURIComponent(loc.pathname + loc.search)
    return <Navigate to={`/login?from=${from}`} replace />
  }
  return <>{children}</>
}

function LoginPage() {
  const { auth, login } = useAuth()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const from = params.get('from') || '/orders'

  const doLogin = (role: 'operator' | 'manager') => {
    login(role === 'manager' ? 'Gerente' : 'Operador', role)
    // Redireciona para a origem desejada (ou /orders)
    navigate(from, { replace: true })
  }

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-2">Login (simulado)</h1>
      {auth.user ? (
        <div className="space-y-2">
          <p className="text-sm text-gray-700">Logado como {auth.user} ({auth.role})</p>
          <Link className="inline-block text-sm text-blue-700 underline" to="/orders">Voltar para pedidos</Link>
        </div>
      ) : (
        <div className="flex gap-2">
          <button className="px-3 py-1 rounded bg-gray-800 text-white" onClick={() => doLogin('operator')}>Entrar como Operador</button>
          <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={() => doLogin('manager')}>Entrar como Gerente</button>
        </div>
      )}
      <p className="mt-2 text-xs text-gray-500">Apenas para demonstração. Integração com backend virá depois.</p>
    </div>
  )
}
