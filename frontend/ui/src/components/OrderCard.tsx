import React from 'react'
import type { Order, OrderStatus } from '../lib/api'
import { statusBadgeClass, statusLabel } from '../i18n/status'
import { useUIConfig } from '../config/provider'

interface Props {
  order: Order
  onChangeStatus?: (orderId: string, next: OrderStatus) => void
  onOpen?: (orderId: string) => void
}

export default function OrderCard({ order, onChangeStatus, onOpen }: Props) {
  const ui = useUIConfig()
  const actions = ui.kanban?.actions?.[order.status] ?? []
  const isTerminal = order.status === 'delivered' || order.status === 'canceled'
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
      {onChangeStatus && !isTerminal && actions.length > 0 && (
        <div className="mt-3 flex gap-2">
          {actions.map((a, idx) => {
              const isCancel = a.next === 'canceled'
              const cls = isCancel
                ? 'text-xs px-2 py-1 rounded bg-red-600 text-white hover:bg-red-700'
                : 'text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700'
              return (
                <button
                  key={`${order.id}-act-${idx}`}
                  className={cls}
                  onClick={(e) => {
                    e.stopPropagation()
                    if (isCancel) {
                      if (!window.confirm('Confirmar cancelamento do pedido?')) return
                    }
                    onChangeStatus(String(order.id), a.next as OrderStatus)
                  }}
                >
                  {a.label}
                </button>
              )
            })}
        </div>
      )}
    </div>
  )
}
