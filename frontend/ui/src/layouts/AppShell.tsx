import React from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import ErrorBoundary from '../components/ErrorBoundary'

export default function AppShell() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-gray-900 text-gray-100 flex-shrink-0">
        <div className="px-4 py-3 text-lg font-semibold border-b border-gray-800">
          <Link to="/">AtendeJá</Link>
        </div>
        <nav className="p-3 space-y-1 text-sm">
          <div className="px-3 py-2 text-xs uppercase tracking-wide text-gray-400">Imobiliário</div>
          <Item to="/imoveis" label="Imóveis" />
          <Item to="/leads" label="Leads" />
          <Item to="/ops" label="Ops" />
        </nav>
      </aside>
      <main className="flex-1 bg-gray-50">
        <div className="p-4">
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
        `block rounded px-3 py-2 hover:bg-gray-800 ${isActive ? 'bg-gray-800 font-medium' : ''}`
      }
    >
      {label}
    </NavLink>
  )
}
