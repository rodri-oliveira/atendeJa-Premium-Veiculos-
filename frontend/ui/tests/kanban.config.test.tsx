/* @vitest-environment jsdom */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import React from 'react'
import { render, screen } from '@testing-library/react'
import KanbanPage from '../src/pages/KanbanPage'
import { ConfigProvider } from '../src/config/provider'

const g: any = globalThis as any

describe('KanbanPage com configuração em runtime', () => {
  beforeEach(() => {
    g.fetch = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/config.json')) {
        return new Response(
          JSON.stringify({
            branding: { appTitle: 'Ops Petshop' },
            kanban: { columns: [{ status: 'draft', title: 'Novo Pedido' }] },
          }),
          { status: 200 }
        )
      }
      if (url.includes('/orders') && (!init || init.method === 'GET')) {
        return new Response(JSON.stringify([{ id: '1', status: 'draft', total_amount: 1 }]), { status: 200 })
      }
      return new Response('', { status: 404 })
    })
  })

  it('usa título e colunas vindos da config', async () => {
    render(
      <ConfigProvider>
        <KanbanPage />
      </ConfigProvider>
    )
    const title = await screen.findByText('Ops Petshop')
    expect(!!title).toBe(true)
    // coluna rebatizada (o header agora inclui contagem, então validamos via data-testid)
    const header = await screen.findByTestId('col-header-draft')
    expect(header.textContent).toContain('Novo Pedido')
  })
})
