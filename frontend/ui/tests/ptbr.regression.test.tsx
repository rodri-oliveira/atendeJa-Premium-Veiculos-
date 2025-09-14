/* @vitest-environment jsdom */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import React from 'react'
import { render, screen } from '@testing-library/react'
import { ConfigProvider } from '../src/config/provider'
import KanbanPage from '../src/pages/KanbanPage'
import OrderDrawer from '../src/components/OrderDrawer'

const g: any = globalThis as any

describe('Regressão de idioma pt-BR na UI', () => {
  beforeEach(() => {
    g.fetch = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/config.json')) {
        return new Response(
          JSON.stringify({
            branding: { appTitle: 'Painel Operacional' },
            kanban: { columns: [{ status: 'draft', title: 'Rascunho' }] },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      }
      if (url.endsWith('/orders/1') && (!init || init.method === 'GET')) {
        return new Response(
          JSON.stringify({
            order_id: 1,
            status: 'draft',
            total_items: 0,
            delivery_fee: 0,
            total_amount: 0,
            delivery_address: {},
            items: [],
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      }
      if (url.endsWith('/orders/1/events')) return new Response(JSON.stringify([]), { status: 200 })
      if (url.endsWith('/orders/1/relation')) return new Response(JSON.stringify({ order_id: 1, source_order_id: null }), { status: 200 })
      if (url.endsWith('/orders/1/reorders')) return new Response(JSON.stringify([]), { status: 200 })
      if (url.endsWith('/orders') && (!init || init.method === 'GET')) {
        return new Response(JSON.stringify([]), { status: 200, headers: { 'Content-Type': 'application/json' } })
      }
      return new Response('', { status: 404 })
    })
    if (typeof g.window !== 'undefined') {
      g.window.ENV = { API_BASE_URL: '/api' }
    }
    // container explícito por consistência
    const root = document.getElementById('root') || document.createElement('div')
    if (!root.id) root.id = 'root'
    if (!root.parentElement) document.body.appendChild(root)
  })

  it('Kanban: exibe rótulos em pt-BR e não mostra termos comuns em inglês', async () => {
    render(
      <ConfigProvider>
        <KanbanPage />
      </ConfigProvider>
    )

    // Presença de rótulos em pt-BR
    expect(await screen.findByText('Atualizar agora')).toBeTruthy()
    expect(await screen.findByText('Limpar filtros')).toBeTruthy()
    const header = await screen.findByTestId('col-header-draft')
    expect(header.textContent).toContain('Rascunho')

    // Ausência de termos comuns em inglês
    const forbidden = [
      'Loading', 'Close', 'Save', 'Update now', 'Search', 'Settings', 'Delivery', 'Customers', 'Menu', 'Refresh', 'Confirm', 'Address'
    ]
    for (const term of forbidden) {
      expect(screen.queryByText(new RegExp(`^${term}$`, 'i'))).toBeNull()
    }
  })

  it('OrderDrawer: botões e mensagens em pt-BR', async () => {
    // Limpa DOM e mocks para evitar interferência de outros testes
    vi.clearAllMocks()
    vi.restoreAllMocks()
    document.body.innerHTML = ''
    // Container isolado para evitar interferência de outros testes
    const container = document.createElement('div')
    document.body.appendChild(container)

    // Mock dedicado para este teste garantindo 200 nos endpoints usados pelo Drawer
    g.fetch = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.includes('/orders/1') && (!init || init.method === 'GET') && !url.includes('/events') && !url.includes('/relation') && !url.includes('/reorders')) {
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
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      }
      if (url.includes('/orders/1/events')) return new Response(JSON.stringify([]), { status: 200 })
      if (url.includes('/orders/1/relation')) return new Response(JSON.stringify({ order_id: 1, source_order_id: null }), { status: 200 })
      if (url.includes('/orders/1/reorders')) return new Response(JSON.stringify([]), { status: 200 })
      return new Response('', { status: 404 })
    })
    if (typeof (g as any).window !== 'undefined') {
      ;(g as any).window.ENV = { API_BASE_URL: '/api' }
    }

    render(<OrderDrawer orderId="1" onClose={() => {}} />, { container })
    // Aguarda conteúdo do Drawer e seção de endereço para garantir montagem completa
    await screen.findByText(/Resumo/i)
    await screen.findByTestId('addr-section')
    const saveBtn = await screen.findByRole('button', { name: /Salvar endereço/i })
    expect(saveBtn).toBeTruthy()
    // Ausência de termos em inglês equivalentes
    expect(screen.queryByText(/^Save address$/i)).toBeNull()
    expect(screen.queryByText(/^Close$/i)).toBeNull()
  })
})
