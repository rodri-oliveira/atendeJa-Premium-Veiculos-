/* @vitest-environment jsdom */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import React from 'react'
import { render, screen } from '@testing-library/react'
import { ConfigCtx, ConfigProvider } from '../src/config/provider'
import type { UIConfig } from '../src/config/schema'

const g: any = globalThis as any

describe('ConfigProvider', () => {
  beforeEach(() => {
    // mock fetch for /config.json
    g.fetch = vi.fn(async (url: string) => {
      if (url.endsWith('/config.json')) {
        const cfg: UIConfig = {
          branding: { appTitle: 'Teste App' },
          kanban: { columns: [{ status: 'draft', title: 'RascunhoX' }] },
        }
        return new Response(JSON.stringify(cfg), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response('', { status: 404 })
    })
  })

  it('carrega config.json e disponibiliza via contexto', async () => {
    function Probe() {
      return (
        <ConfigProvider>
          <ConfigCtx.Consumer>
            {(cfg) => (
              <div>
                <div data-testid="title">{cfg.branding?.appTitle}</div>
                <div data-testid="col0">{cfg.kanban?.columns?.[0]?.title}</div>
              </div>
            )}
          </ConfigCtx.Consumer>
        </ConfigProvider>
      )
    }

    render(<Probe />)

    const title = await screen.findByTestId('title')
    expect(title.textContent).toBe('Teste App')
    const col0 = await screen.findByTestId('col0')
    expect(col0.textContent).toBe('RascunhoX')
  })
})
