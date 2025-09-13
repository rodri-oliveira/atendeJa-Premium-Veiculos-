export type OrderStatus =
  | 'draft'
  | 'pending_payment'
  | 'paid'
  | 'in_kitchen'
  | 'out_for_delivery'
  | 'delivered'
  | 'canceled'

export interface ListOrdersQuery {
  status?: OrderStatus
  search?: string
  limit?: number
  since?: string
  until?: string
}

// Define/atualiza o endereço do pedido (requerido para confirmar)
export async function setOrderAddress(orderId: string, address: Address): Promise<OrderDetails> {
  const url = `${API_BASE()}/orders/${encodeURIComponent(orderId)}?op=set_address`
  const res = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ address }),
  })
  if (!res.ok) {
    try {
      const body = await res.json()
      const detail = (body && (body.detail || body.message)) ? ` - ${body.detail || body.message}` : ''
      throw new Error(`setOrderAddress failed: ${res.status}${detail}`)
    } catch {
      try {
        const text = await res.text()
        const suffix = text ? ` - ${text}` : ''
        throw new Error(`setOrderAddress failed: ${res.status}${suffix}`)
      } catch {
        throw new Error(`setOrderAddress failed: ${res.status}`)
      }
    }
  }
  return res.json()
}

export interface Order {
  id: string
  status: OrderStatus
  created_at?: string
  total_amount?: number
  total_items?: number
}

export interface OrderItem {
  id: number
  menu_item_id: number
  qty: number
  unit_price: number
  options?: Record<string, any> | null
}

export interface OrderDetails {
  order_id: number
  status: OrderStatus
  total_items?: number
  delivery_fee?: number
  total_amount?: number
  delivery_address?: Record<string, any> | null
  items: OrderItem[]
}

export interface Address {
  street: string
  number: string
  district: string
  city: string
  state: string
  cep: string
}

export interface OrderEvent {
  id: number
  order_id: number
  from_status: string
  to_status: string
  created_at: string
}

export interface OrderRelationInfo {
  order_id: number
  source_order_id: number | null
}

const API_BASE = () => (window as any).ENV?.API_BASE_URL || 'http://localhost:8000'

export async function listOrders(q: ListOrdersQuery = {}): Promise<Order[]> {
  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(q)) {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v))
  }
  const url = `${API_BASE()}/orders${params.toString() ? `?${params.toString()}` : ''}`
  const res = await fetch(url, { cache: 'no-store', method: 'GET' })
  if (!res.ok) throw new Error(`listOrders failed: ${res.status}`)
  return res.json()
}

export async function setOrderStatus(orderId: string, next: OrderStatus): Promise<Order> {
  const url = `${API_BASE()}/orders/${encodeURIComponent(orderId)}/status`
  const res = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: next }),
  })
  if (!res.ok) {
    try {
      const body = await res.json()
      const detail = (body && (body.detail || body.message)) ? ` - ${body.detail || body.message}` : ''
      throw new Error(`setOrderStatus failed: ${res.status}${detail}`)
    } catch {
      try {
        const text = await res.text()
        const suffix = text ? ` - ${text}` : ''
        throw new Error(`setOrderStatus failed: ${res.status}${suffix}`)
      } catch {
        throw new Error(`setOrderStatus failed: ${res.status}`)
      }
    }
  }
  return res.json()
}

// Confirma um pedido em rascunho, movendo para pending_payment conforme regra do backend
export async function confirmOrder(orderId: string): Promise<OrderDetails> {
  const url = `${API_BASE()}/orders/${encodeURIComponent(orderId)}?op=confirm`
  const res = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirm: true }),
  })
  if (!res.ok) {
    try {
      const body = await res.json()
      const detail = (body && (body.detail || body.message)) ? ` - ${body.detail || body.message}` : ''
      throw new Error(`confirmOrder failed: ${res.status}${detail}`)
    } catch {
      try {
        const text = await res.text()
        const suffix = text ? ` - ${text}` : ''
        throw new Error(`confirmOrder failed: ${res.status}${suffix}`)
      } catch {
        throw new Error(`confirmOrder failed: ${res.status}`)
      }
    }
  }
  return res.json()
}

export async function getOrder(orderId: string): Promise<OrderDetails> {
  const url = `${API_BASE()}/orders/${encodeURIComponent(orderId)}`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`getOrder failed: ${res.status}`)
  return res.json()
}

export async function getOrderEvents(orderId: string): Promise<OrderEvent[]> {
  const url = `${API_BASE()}/orders/${encodeURIComponent(orderId)}/events`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`getOrderEvents failed: ${res.status}`)
  return res.json()
}

export async function getOrderRelation(orderId: string): Promise<OrderRelationInfo> {
  const url = `${API_BASE()}/orders/${encodeURIComponent(orderId)}/relation`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`getOrderRelation failed: ${res.status}`)
  return res.json()
}

export async function getOrderReorders(orderId: string): Promise<Order[]> {
  const url = `${API_BASE()}/orders/${encodeURIComponent(orderId)}/reorders`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`getOrderReorders failed: ${res.status}`)
  return res.json()
}
