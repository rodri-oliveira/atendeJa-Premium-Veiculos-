import React from 'react'
import type { Order, OrderStatus } from '../lib/api'
import { statusBadgeClass, statusLabel } from '../i18n/status'
import { useUIConfig } from '../config/provider'

interface Props {
  order: Order
  onChangeStatus?: (orderId: string, next: OrderStatus) => void
  onOpen?: (orderId: string) => void
  busy?: boolean
  compact?: boolean
}

export default function OrderCard({ order, onChangeStatus, onOpen, busy, compact = false }: Props) {
  const ui = useUIConfig()
  const actions = ui.kanban?.actions?.[order.status] ?? []
  const isTerminal = order.status === 'delivered' || order.status === 'canceled'
  return (
    <div className={`rounded border ${compact ? 'p-2' : 'p-3'} bg-white shadow-sm`}
    >
      <div
        className={`flex items-center justify-between cursor-pointer ${compact ? 'gap-2' : ''}`}
        onClick={() => onOpen?.(String(order.id))}
        role="button"
        aria-label={`Abrir detalhes do pedido ${order.id}`}
      >
        <span className={`inline-block ${compact ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs'} rounded ${statusBadgeClass(order.status)}`}>
          {statusLabel(order.status)}
        </span>
        <span className={`${compact ? 'text-[10px]' : 'text-xs'} text-gray-500`}>#{order.id}</span>
      </div>
      <div className={`${compact ? 'mt-1 text-xs' : 'mt-2 text-sm'} text-gray-700`}>Total: R$ {Number(order.total_amount ?? 0).toFixed(2)}
        {!compact && typeof order.total_items !== 'undefined' && (
          <div className="text-xs text-gray-600">Itens: {order.total_items}</div>
        )}
      </div>
      {onChangeStatus && !isTerminal && actions.length > 0 && (
        <div className={`${compact ? 'mt-2' : 'mt-3'} flex gap-2`}
        >
          {actions.map((a, idx) => {
              const isCancel = a.next === 'canceled'
              const base = compact ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-1'
              const cls = isCancel
                ? `${base} rounded bg-red-600 text-white hover:bg-red-700`
                : `${base} rounded bg-blue-600 text-white hover:bg-blue-700`
              return (
                <button
                  key={`${order.id}-act-${idx}`}
                  className={`${cls} disabled:opacity-50 disabled:cursor-not-allowed`}
                  disabled={!!busy}
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
