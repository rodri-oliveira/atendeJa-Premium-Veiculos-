import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppShell from './layouts/AppShell'
import OpsDashboard from './pages/OpsDashboard'
import About from './pages/About'
import Login from './pages/Login'
import UsersAdmin from './pages/UsersAdmin'
import RequireAuth from './components/RequireAuth'
import Reports from './pages/Reports'
import VehiclesList from './pages/VehiclesList'
import VehicleDetalhes from './pages/VehicleDetalhes'
import LeadsList from './pages/LeadsList'
import Financiamento from './pages/Financiamento'
import ImportCsv from './pages/ImportCsv'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}> 
          <Route index element={<Navigate to="/veiculos" replace />} />
          <Route path="veiculos" element={<VehiclesList />} />
          <Route path="veiculos/:id" element={<VehicleDetalhes />} />
          <Route path="financiamento" element={<Financiamento />} />
          <Route path="import" element={<RequireAuth><ImportCsv /></RequireAuth>} />
          <Route path="leads" element={<RequireAuth><LeadsList /></RequireAuth>} />
          <Route path="ops" element={<OpsDashboard />} />
          <Route path="reports" element={<RequireAuth><Reports /></RequireAuth>} />
          <Route path="users" element={<RequireAuth><UsersAdmin /></RequireAuth>} />
          <Route path="sobre" element={<About />} />
          <Route path="*" element={<Navigate to="/veiculos" replace />} />
        </Route>
        <Route path="/login" element={<Login />} />
      </Routes>
    </BrowserRouter>
  )
}
