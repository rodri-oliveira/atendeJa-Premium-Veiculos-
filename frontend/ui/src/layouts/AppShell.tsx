import React from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import ErrorBoundary from '../components/ErrorBoundary'

export default function AppShell() {
  return (
    <div className="min-h-screen flex bg-slate-50">
      <aside className="w-64 bg-gradient-to-b from-slate-800 to-slate-900 text-white flex-shrink-0 shadow-xl">
        <div className="px-6 py-5 border-b border-slate-700">
          <Link to="/" className="flex items-center space-x-3 hover:opacity-90 transition-opacity">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">ND</span>
            </div>
            <div>
              <div className="text-lg font-bold">AtendeJá</div>
              <div className="text-xs text-slate-300">ND Imóveis</div>
            </div>
          </Link>
        </div>
        <nav className="p-4 space-y-2">
          <div className="px-3 py-2 text-xs uppercase tracking-wide text-slate-400 font-semibold">Imobiliário</div>
          <Item to="/imoveis" label="Imóveis" />
          <Item to="/import" label="Importar CSV" />
          <Item to="/leads" label="Leads" />
          <Item to="/ops" label="Operações" />
          <Item to="/sobre" label="Sobre" />
        </nav>
      </aside>
      <main className="flex-1 bg-slate-50">
        <div className="p-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </div>
      </main>
    </div>
  )
}

function Item({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }: { isActive: boolean }) =>
        `group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
          isActive
            ? 'bg-primary-600 text-white shadow-lg shadow-primary-600/25'
            : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
        }`
      }
    >
      {({ isActive }: { isActive: boolean }) => (
        <>
          <span className="truncate">{label}</span>
          {/* Indicador visual para item ativo */}
          <div
            className={`ml-auto w-1 h-4 rounded-full transition-opacity ${
              isActive ? 'opacity-100 bg-primary-300' : 'opacity-0'
            }`}
          />
        </>
      )}
    </NavLink>
  )
}
