import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

type Role = 'operator' | 'manager'

export type AuthState = {
  user: string | null
  role: Role | null
}

type AuthContextType = {
  auth: AuthState
  login: (user: string, role: Role) => void
  logout: () => void
}

const defaultAuth: AuthState = { user: null, role: null }

const AuthCtx = createContext<AuthContextType>({
  auth: defaultAuth,
  login: () => {},
  logout: () => {},
})

export function useAuth() {
  return useContext(AuthCtx)
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState>(defaultAuth)

  useEffect(() => {
    try {
      const raw = localStorage.getItem('atendeja.auth')
      if (raw) {
        const parsed = JSON.parse(raw) as AuthState
        setAuth(parsed)
      }
    } catch {
      console.warn('AuthProvider: falha ao ler auth do localStorage')
    }
  }, [])

  const api = useMemo<AuthContextType>(() => ({
    auth,
    login: (user: string, role: Role) => {
      const next: AuthState = { user, role }
      setAuth(next)
      try { localStorage.setItem('atendeja.auth', JSON.stringify(next)) } catch {
        console.warn('AuthProvider: falha ao salvar auth no localStorage')
      }
    },
    logout: () => {
      setAuth(defaultAuth)
      try { localStorage.removeItem('atendeja.auth') } catch {
        console.warn('AuthProvider: falha ao limpar auth do localStorage')
      }
    },
  }), [auth])

  return <AuthCtx.Provider value={api}>{children}</AuthCtx.Provider>
}
