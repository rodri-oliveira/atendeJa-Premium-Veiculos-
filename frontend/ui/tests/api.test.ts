import { describe, it, expect, vi, beforeEach } from 'vitest'
import { listOrders, setOrderStatus } from '../src/lib/api'

const g: any = globalThis as any

describe('api client', () => {
  beforeEach(() => {
    g.fetch = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.includes('/orders') && (!init || init.method === 'GET')) {
        return new Response(JSON.stringify([]), { status: 200 })
      }
      if (url.includes('/status') && init?.method === 'PATCH') {
        return new Response(JSON.stringify({ id: '1', status: 'in_kitchen', created_at: '' }), { status: 200 })
      }
      return new Response('', { status: 404 })
    })
    ;(g as any).window = { ENV: { API_BASE_URL: 'http://api:8000' } }
  })

  it('monta URL com query params em listOrders', async () => {
    await listOrders({ status: 'draft', limit: 10 })
    expect(g.fetch).toHaveBeenCalled()
    const [url] = (g.fetch as any).mock.calls[0]
    expect(url).toContain('http://api:8000/orders?')
    expect(url).toContain('status=draft')
    expect(url).toContain('limit=10')
  })

  it('PATCH setOrderStatus', async () => {
    await setOrderStatus('1', 'in_kitchen')
    const [, init] = (g.fetch as any).mock.calls[0]
    expect(init.method).toBe('PATCH')
    expect(JSON.parse(init.body as string)).toEqual({ status: 'in_kitchen' })
  })
})
