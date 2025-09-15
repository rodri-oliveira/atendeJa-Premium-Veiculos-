// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import OpsDashboard from '../src/pages/OpsDashboard'

describe('OpsDashboard', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('exibe config e ping meta', async () => {
    const mockConfig = {
      app_env: 'dev', wa_provider: 'meta', default_tenant: 'default', re_read_only: false, version: '0.1.0'
    }
    const mockPing = { env_ok: true, graph_reachable: true, graph_head_status: 400 }

    vi.spyOn(globalThis, 'fetch' as any)
      .mockResolvedValueOnce({ ok: true, json: async () => mockConfig } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => mockPing } as Response)

    render(
      <MemoryRouter initialEntries={["/ops"]}>
        <OpsDashboard />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Operações')).toBeTruthy()
      expect(screen.getByText('dev')).toBeTruthy()
      expect(screen.getByText('meta')).toBeTruthy()
      // existem dois 'true' (env_ok e graph_reachable)
      const trues = screen.getAllByText('true')
      expect(trues.length).toBeGreaterThanOrEqual(2)
      expect(screen.getByText('400')).toBeTruthy()
    })
  })
})
