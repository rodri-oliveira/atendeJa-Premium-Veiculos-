import React from 'react'
import type { Order, OrderStatus } from '../lib/api'
import { statusBadgeClass, statusLabel } from '../i18n/status'

interface Props {
  order: Order
  onChangeStatus?: (orderId: string, next: OrderStatus) => void
  onOpen?: (orderId: string) => void
}

export default function OrderCard({ order, onChangeStatus, onOpen }: Props) {
  return (
    <div className="rounded border p-3 bg-white shadow-sm">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => onOpen?.(String(order.id))}
        role="button"
        aria-label={`Abrir detalhes do pedido ${order.id}`}
      >
        <span className={`inline-block px-2 py-0.5 rounded text-xs ${statusBadgeClass(order.status)}`}>
          {statusLabel(order.status)}
        </span>
        <span className="text-xs text-gray-500">#{order.id}</span>
      </div>
      <div className="mt-2 text-sm text-gray-700">
        Total: R$ {Number(order.total_amount ?? 0).toFixed(2)}
      </div>
      {onChangeStatus && (
        <div className="mt-3 flex gap-2">
          {/* Exemplo simples: avançar para próximo estado operacional */}
          <button
            className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
            onClick={() => onChangeStatus(String(order.id), 'in_kitchen')}
          >
            Marcar em preparo
          </button>
        </div>
      )}
    </div>
  )
}
