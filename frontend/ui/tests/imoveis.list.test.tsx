// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ImoveisList from '../src/pages/ImoveisList'

const mockImoveis = [
  {
    id: 1,
    titulo: 'Apto 2 dorm SP',
    tipo: 'apartment',
    finalidade: 'rent',
    preco: 3000,
    cidade: 'São Paulo',
    estado: 'SP',
    dormitorios: 2,
    ativo: true,
  },
]

describe('ImoveisList', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renderiza título e carrega lista', async () => {
    vi.spyOn(globalThis, 'fetch' as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockImoveis,
    } as Response)

    render(
      <MemoryRouter initialEntries={["/imoveis"]}>
        <ImoveisList />
      </MemoryRouter>
    )

    // título
    const title = await screen.findByText('Imóveis')
    expect(title).toBeTruthy()

    // card carregado
    await waitFor(() => {
      expect(screen.getByText('Apto 2 dorm SP')).toBeTruthy()
      expect(screen.getByText('R$ 3.000')).toBeTruthy()
    })
  })
})
