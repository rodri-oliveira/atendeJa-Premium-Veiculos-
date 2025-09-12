import type { OrderStatus } from '../lib/api'

export const statusPtBr: Record<OrderStatus, string> = {
  draft: 'Rascunho',
  pending_payment: 'Aguardando pagamento',
  paid: 'Pago',
  in_kitchen: 'Em preparo',
  out_for_delivery: 'Saiu para entrega',
  delivered: 'Entregue',
  canceled: 'Cancelado',
}

export type StatusBadge = 'gray' | 'yellow' | 'blue' | 'purple' | 'orange' | 'green' | 'red'

export const statusBadge: Record<OrderStatus, StatusBadge> = {
  draft: 'gray',
  pending_payment: 'yellow',
  paid: 'blue',
  in_kitchen: 'purple',
  out_for_delivery: 'orange',
  delivered: 'green',
  canceled: 'red',
}

export function statusLabel(s: OrderStatus): string {
  return statusPtBr[s] ?? s
}

export function statusBadgeClass(s: OrderStatus): string {
  const map: Record<StatusBadge, string> = {
    gray: 'bg-gray-100 text-gray-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    blue: 'bg-blue-100 text-blue-800',
    purple: 'bg-purple-100 text-purple-800',
    orange: 'bg-orange-100 text-orange-800',
    green: 'bg-green-100 text-green-800',
    red: 'bg-red-100 text-red-800',
  }
  return map[statusBadge[s]]
}
