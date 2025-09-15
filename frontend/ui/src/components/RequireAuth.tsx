import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { isAuthenticated } from '../lib/auth'

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const authed = isAuthenticated()
  const location = useLocation()
  if (!authed) {
    return <Navigate to="/login" replace state={{ redirectTo: location.pathname + location.search }} />
  }
  return <>{children}</>
}
