export function getToken(): string | null {
  try {
    return localStorage.getItem('auth_token')
  } catch {
    return null
  }
}

export function setToken(token: string) {
  try {
    localStorage.setItem('auth_token', token)
  } catch {}
}

export function clearToken() {
  try {
    localStorage.removeItem('auth_token')
  } catch {}
}

export function isAuthenticated(): boolean {
  const t = getToken()
  return !!t && t.length > 10
}

export async function apiFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const url = input
  const headers = new Headers(init.headers || {})

  // Adiciona Authorization automaticamente para qualquer rota da API quando houver token
  if (url.startsWith('/api/')) {
    const token = getToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  return fetch(url, { ...init, headers })
}
