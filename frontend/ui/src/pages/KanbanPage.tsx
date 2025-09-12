import React, { useEffect, useMemo, useState } from 'react'
import { listOrders, type Order, type OrderStatus, setOrderStatus } from '../lib/api'
import FiltersBar from '../components/FiltersBar'
import OrderCard from '../components/OrderCard'
import { useUIConfig } from '../config/provider'
import OrderDrawer from '../components/OrderDrawer'

export default function KanbanPage() {
  const [status, setStatus] = useState<OrderStatus | undefined>()
  const [search, setSearch] = useState<string>('')
  const [limit, setLimit] = useState<number>(50)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [orders, setOrders] = useState<Order[]>([])
  const ui = useUIConfig()
  const [selected, setSelected] = useState<string | null>(null)
  const [pauseUntilMs, setPauseUntilMs] = useState<number>(0)

  const COLUMNS = useMemo(() => {
    return (ui.kanban?.columns || []).map((c) => ({ key: c.status as OrderStatus, title: c.title }))
  }, [ui])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const rows = await listOrders({ status, search: search || undefined, limit })
      setOrders(rows)
    } catch (e: any) {
      setError(e?.message || 'Erro ao carregar pedidos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const id = setInterval(() => {
      if (Date.now() >= pauseUntilMs) {
        fetchData()
      }
    }, 10_000) // auto-refresh a cada 10s
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, search, limit, pauseUntilMs])

  const groups = useMemo(() => {
    const map = new Map<OrderStatus, Order[]>()
    for (const c of COLUMNS) map.set(c.key, [])
    for (const o of orders) {
      const bucket = map.get(o.status)
      if (bucket) bucket.push(o)
    }
    return map
  }, [orders])

  const onChangeFilters = (next: { status?: OrderStatus; search?: string; limit?: number }) => {
    if ('status' in next) setStatus(next.status)
    if (typeof next.search !== 'undefined') setSearch(next.search || '')
    if (typeof next.limit !== 'undefined') setLimit(next.limit || 50)

    // Dispara refetch imediato usando os valores recebidos (evita esperar o próximo render)
    ;(async () => {
      try {
        setLoading(true)
        setError(null)
        const effectiveStatus = ('status' in next) ? next.status : status
        const effectiveSearch = (typeof next.search !== 'undefined') ? (next.search || '') : search
        const effectiveLimit = (typeof next.limit !== 'undefined') ? (next.limit || 50) : limit
        const rows = await listOrders({ status: effectiveStatus, search: effectiveSearch || undefined, limit: effectiveLimit })
        setOrders(rows)
      } catch (e: any) {
        setError(e?.message || 'Erro ao carregar pedidos')
      } finally {
        setLoading(false)
      }
    })()

    // Pausa o auto-refresh por 5s após alterações de filtro para evitar corrida com o refresh periódico
    setPauseUntilMs(Date.now() + 5_000)
  }

  const handleChangeStatus = async (orderId: string, next: OrderStatus) => {
    try {
      await setOrderStatus(orderId, next)
      fetchData()
    } catch (e) {
      console.error(e)
      setError('Falha ao alterar status')
    }
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-3">{ui.branding?.appTitle || 'Painel Operacional'}</h1>
      <FiltersBar status={status} search={search} limit={limit} onChange={onChangeFilters} />
      {error && <div className="mt-3 text-sm text-red-700">{error}</div>}
      {loading && <div className="mt-3 text-sm text-gray-600">Carregando...</div>}
      <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-4 gap-4 mt-4">
        {COLUMNS.map((col) => (
          <div key={col.key} className="bg-gray-50 border rounded p-2" data-testid={`col-${col.key}`}>
            <div className="font-semibold text-sm mb-2" data-testid={`col-header-${col.key}`}>{col.title}</div>
            <div className="flex flex-col gap-2">
              {(groups.get(col.key) || []).map((o) => (
                <OrderCard key={o.id} order={o} onChangeStatus={handleChangeStatus} onOpen={(id) => setSelected(id)} />
              ))}
            </div>
          </div>
        ))}
      </div>
      {selected && <OrderDrawer orderId={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
