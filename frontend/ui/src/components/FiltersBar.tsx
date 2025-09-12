import React from 'react'
import type { OrderStatus } from '../lib/api'

interface Props {
  status?: OrderStatus
  search?: string
  limit?: number
  onChange: (next: { status?: OrderStatus; search?: string; limit?: number }) => void
}

const STATUS_OPTIONS: { value?: OrderStatus; label: string }[] = [
  { value: undefined, label: 'Todos' },
  { value: 'draft', label: 'Rascunho' },
  { value: 'pending_payment', label: 'Aguardando pagamento' },
  { value: 'paid', label: 'Pago' },
  { value: 'in_kitchen', label: 'Em preparo' },
  { value: 'out_for_delivery', label: 'Saiu para entrega' },
  { value: 'delivered', label: 'Entregue' },
  { value: 'canceled', label: 'Cancelado' },
]

export default function FiltersBar({ status, search, limit = 50, onChange }: Props) {
  return (
    <div className="flex flex-wrap items-end gap-3 p-3 bg-gray-50 border rounded">
      <div className="flex flex-col">
        <label className="text-xs text-gray-600">Status</label>
        <select
          className="border rounded px-2 py-1"
          value={status ?? ''}
          onChange={(e) => {
            const val = e.target.value as string
            onChange({ status: (val === '' ? undefined : (val as OrderStatus)), search, limit })
          }}
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.label} value={o.value ?? ''}>{o.label}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col">
        <label className="text-xs text-gray-600">Busca</label>
        <input
          className="border rounded px-2 py-1"
          placeholder="Telefone/WA"
          value={search ?? ''}
          onChange={(e) => onChange({ search: e.target.value })}
        />
      </div>

      <div className="flex flex-col">
        <label className="text-xs text-gray-600">Limite</label>
        <input
          className="border rounded px-2 py-1 w-24"
          type="number"
          min={1}
          max={200}
          value={limit}
          onChange={(e) => onChange({ limit: Number(e.target.value) })}
        />
      </div>

      <div className="flex-1" />
      <button
        className="text-sm px-3 py-1 border rounded"
        onClick={() => onChange({ status: undefined, search: '', limit: 50 })}
        type="button"
      >
        Limpar filtros
      </button>
    </div>
  )
}
