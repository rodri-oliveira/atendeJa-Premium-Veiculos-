/* @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import OrderDrawer from '../src/components/OrderDrawer'

const g: any = globalThis as any

describe('OrderDrawer', () => {
  beforeEach(() => {
    // container explícito
    const root = document.createElement('div')
    root.setAttribute('id', 'root')
    document.body.appendChild(root)

    g.fetch = vi.fn(async (url: string) => {
      if (url.endsWith('/orders/1')) {
        return new Response(
          JSON.stringify({
            order_id: 1,
            status: 'draft',
            total_items: 2,
            delivery_fee: 0,
            total_amount: 10,
            delivery_address: { city: 'São Paulo', street: 'Rua A' },
            items: [
              { id: 1, menu_item_id: 100, qty: 1, unit_price: 5 },
              { id: 2, menu_item_id: 101, qty: 1, unit_price: 5 },
            ],
          }),
          { status: 200 }
        )
      }
      if (url.endsWith('/orders/1/events')) {
        return new Response(
          JSON.stringify([
            { id: 1, order_id: 1, from_status: 'draft', to_status: 'draft', created_at: '2024-01-01T00:00:00Z' },
          ]),
          { status: 200 }
        )
      }
      if (url.endsWith('/orders/1/relation')) {
        return new Response(JSON.stringify({ order_id: 1, source_order_id: null }), { status: 200 })
      }
      if (url.endsWith('/orders/1/reorders')) {
        return new Response(JSON.stringify([]), { status: 200 })
      }
      return new Response('', { status: 404 })
    })
    if (typeof (g as any).window !== 'undefined') {
      ;(g as any).window.ENV = { API_BASE_URL: '/api' }
    }
  })

  it('carrega e exibe detalhes do pedido', async () => {
    const onClose = vi.fn()
    const container = document.getElementById('root') as HTMLElement
    render(<OrderDrawer orderId="1" onClose={onClose} />, { container })
    // loading
    expect(screen.getByText(/Carregando/i)).toBeTruthy()
    // detalhes
    await waitFor(() => {
      expect(screen.getByText(/Resumo/i)).toBeTruthy()
      expect(screen.getByText(/Total: R\$ 10.00/i)).toBeTruthy()
      expect(screen.getByText(/Eventos/i)).toBeTruthy()
    })
  })

  it('fecha ao clicar no overlay', async () => {
    const onClose = vi.fn()
    const container = document.getElementById('root') as HTMLElement
    render(<OrderDrawer orderId="1" onClose={onClose} />, { container })
    await screen.findByText(/Resumo/i)
    const overlay = document.querySelector('.fixed.inset-0.z-50 > .absolute.inset-0') as HTMLElement
    fireEvent.click(overlay)
    expect(onClose).toHaveBeenCalled()
  })

  it('fecha ao pressionar ESC', async () => {
    const onClose = vi.fn()
    const container = document.getElementById('root') as HTMLElement
    render(<OrderDrawer orderId="1" onClose={onClose} />, { container })
    await screen.findByText(/Resumo/i)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })
})
