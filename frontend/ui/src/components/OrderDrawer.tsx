import React, { useEffect, useState } from 'react'
import { getOrder, getOrderEvents, getOrderRelation, getOrderReorders, type OrderDetails, type OrderEvent, type Order } from '../lib/api'

interface Props {
  orderId: string
  onClose: () => void
}

export default function OrderDrawer({ orderId, onClose }: Props) {
  const [details, setDetails] = useState<OrderDetails | null>(null)
  const [events, setEvents] = useState<OrderEvent[] | null>(null)
  const [relation, setRelation] = useState<{ source_order_id: number | null } | null>(null)
  const [reorders, setReorders] = useState<Order[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    const load = async () => {
      try {
        setError(null)
        const [d, ev, rel, rorders] = await Promise.all([
          getOrder(orderId),
          getOrderEvents(orderId),
          getOrderRelation(orderId),
          getOrderReorders(orderId),
        ])
        if (!alive) return
        setDetails(d)
        setEvents(ev)
        setRelation(rel)
        setReorders(rorders)
      } catch (e: any) {
        if (!alive) return
        setError(e?.message || 'Falha ao carregar detalhes')
      }
    }
    load()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => {
      alive = false
      window.removeEventListener('keydown', onKey)
    }
  }, [orderId, onClose])

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="absolute right-0 top-0 h-full w-full sm:w-[480px] bg-white shadow-xl overflow-auto">
        <div className="flex items-center justify-between p-3 border-b">
          <h2 className="font-semibold">Pedido #{orderId}</h2>
          <button className="text-sm px-2 py-1 border rounded" onClick={onClose}>Fechar</button>
        </div>
        {error && <div className="p-3 text-sm text-red-700">{error}</div>}
        {!details && !error && (
          <div className="p-3 text-sm text-gray-600">Carregando...</div>
        )}
        {details && (
          <div className="p-3 space-y-4">
            <section>
              <h3 className="font-semibold mb-1">Resumo</h3>
              <div className="text-sm text-gray-700">
                Status: <b>{details.status}</b><br/>
                Total itens: {details.total_items ?? 0}<br/>
                Taxa entrega: R$ {Number(details.delivery_fee ?? 0).toFixed(2)}<br/>
                Total: R$ {Number(details.total_amount ?? 0).toFixed(2)}
              </div>
            </section>
            <section>
              <h3 className="font-semibold mb-1">Itens</h3>
              <ul className="text-sm list-disc ml-4">
                {details.items.map(it => (
                  <li key={it.id}>#{it.menu_item_id} x{it.qty} — R$ {Number(it.unit_price).toFixed(2)}</li>
                ))}
              </ul>
            </section>
            <section>
              <h3 className="font-semibold mb-1">Endereço</h3>
              <div className="text-sm text-gray-700">
                {details.delivery_address ? (
                  <pre className="bg-gray-50 p-2 rounded overflow-auto text-xs">{JSON.stringify(details.delivery_address, null, 2)}</pre>
                ) : '—'}
              </div>
            </section>
            <section>
              <h3 className="font-semibold mb-1">Eventos</h3>
              <ul className="text-sm list-disc ml-4">
                {(events || []).map(ev => (
                  <li key={ev.id}>{ev.created_at}: {ev.from_status} → {ev.to_status}</li>
                ))}
              </ul>
            </section>
            <section>
              <h3 className="font-semibold mb-1">Relação</h3>
              <div className="text-sm text-gray-700">Origem: {relation?.source_order_id ?? '—'}</div>
            </section>
            <section>
              <h3 className="font-semibold mb-1">Reorders</h3>
              <ul className="text-sm list-disc ml-4">
                {(reorders || []).map(r => (
                  <li key={r.id}>#{r.id} — {r.status}</li>
                ))}
              </ul>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}
