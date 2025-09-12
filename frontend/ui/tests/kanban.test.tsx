/* @vitest-environment jsdom */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import KanbanPage from '../src/pages/KanbanPage'

const g: any = globalThis as any

describe('KanbanPage', () => {
  beforeEach(() => {
    // container explícito anexado ao body
    const root = document.createElement('div')
    root.setAttribute('id', 'root')
    document.body.appendChild(root)

    g.fetch = vi.fn(async (url: string) => {
      if (url.includes('/orders')) {
        return new Response(
          JSON.stringify([
            { id: '1', status: 'draft', total_amount: 10 },
            { id: '2', status: 'in_kitchen', total_amount: 25.5 },
          ]),
          { status: 200 }
        )
      }
      return new Response('', { status: 404 })
    })
    if (typeof (g as any).window !== 'undefined') {
      ;(g as any).window.ENV = { API_BASE_URL: 'http://api:8000' }
    }
  })

  it('renderiza colunas e cards básicos', async () => {
    const container = document.getElementById('root') as HTMLElement
    render(<KanbanPage />, { container })
    // Títulos das colunas
    // Pode aparecer tanto no título da coluna quanto no badge do card
    const rascunhos = await screen.findAllByText('Rascunho')
    expect(rascunhos.length).toBeGreaterThan(0)
    const emPreparo = screen.getAllByText('Em preparo')
    expect(emPreparo.length).toBeGreaterThan(0)

    // Aguarda fetch popular cards
    await waitFor(() => {
      expect(screen.getAllByText(/Total: R\$/).length).toBeGreaterThan(0)
    })
  })
})
