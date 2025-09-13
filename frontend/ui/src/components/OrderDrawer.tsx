import React, { useEffect, useState } from 'react'
import { getOrder, getOrderEvents, getOrderRelation, getOrderReorders, confirmOrder, setOrderAddress, type OrderDetails, type OrderEvent, type Order, type Address } from '../lib/api'

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
  const [busy, setBusy] = useState<boolean>(false)
  const [addr, setAddr] = useState<Address | null>(null)
  const [addrErrors, setAddrErrors] = useState<Record<string, string>>({})

  const validateAddr = (a: Address | null) => {
    const errs: Record<string, string> = {}
    if (!a) return errs
    if (!a.street?.trim()) errs.street = 'Informe a rua'
    if (!a.number?.trim()) errs.number = 'Informe o número'
    if (!a.city?.trim()) errs.city = 'Informe a cidade'
    if (!a.state?.trim()) errs.state = 'Informe UF'
    if (a.state && !/^([A-Za-z]{2})$/.test(a.state.trim())) errs.state = 'UF deve ter 2 letras'
    if (!a.cep?.trim()) errs.cep = 'Informe o CEP'
    if (a.cep && !/^\d{5}-?\d{3}$/.test(a.cep.trim())) errs.cep = 'CEP deve ser 00000-000'
    return errs
  }

  const formatCep = (value: string) => {
    const digits = (value || '').replace(/\D/g, '').slice(0, 8)
    if (digits.length <= 5) return digits
    return `${digits.slice(0,5)}-${digits.slice(5)}`
  }

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
        try {
          const a = (d?.delivery_address || {}) as any
          if (a && (a.street || a.number || a.city)) {
            setAddr({
              street: a.street || '',
              number: a.number || '',
              district: a.district || '',
              city: a.city || '',
              state: a.state || '',
              cep: a.cep || '',
            })
          } else {
            setAddr({ street: '', number: '', district: '', city: '', state: '', cep: '' })
          }
        } catch {
          setAddr({ street: '', number: '', district: '', city: '', state: '', cep: '' })
        }
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
            {details.status === 'draft' && (
              <section>
                <h3 className="font-semibold mb-2">Ações</h3>
                <div className="flex gap-2">
                  <button
                    className="text-sm px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                    disabled={busy}
                    onClick={async () => {
                      try {
                        setBusy(true)
                        setError(null)
                        await confirmOrder(orderId)
                        // reload details após confirmar
                        const d = await getOrder(orderId)
                        setDetails(d)
                      } catch (e: any) {
                        setError(e?.message || 'Falha ao confirmar pedido')
                      } finally {
                        setBusy(false)
                      }
                    }}
                  >
                    Confirmar pedido (Aguardando pagamento)
                  </button>
                </div>
                <p className="text-xs text-gray-600 mt-2">
                  Para confirmar, é necessário endereço válido no pedido. Caso veja o erro "address_required", preencha o endereço antes.
                </p>
              </section>
            )}
            {details.status === 'draft' && (
              <section>
                <h3 className="font-semibold mb-2">Endereço (obrigatório para confirmar)</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <label className="col-span-2">
                    Rua
                    <input
                      className={`mt-1 w-full border rounded px-2 py-1 ${addrErrors.street ? 'border-red-500' : ''}`}
                      value={addr?.street || ''}
                      onChange={(e)=>{
                        const next = { ...(addr||{street:'',number:'',district:'',city:'',state:'',cep:''}), street: e.target.value }
                        setAddr(next as Address)
                        setAddrErrors(validateAddr(next as Address))
                      }}
                    />
                    {addrErrors.street && <span className="text-xs text-red-600">{addrErrors.street}</span>}
                  </label>
                  <label>
                    Número
                    <input
                      className={`mt-1 w-full border rounded px-2 py-1 ${addrErrors.number ? 'border-red-500' : ''}`}
                      value={addr?.number || ''}
                      onChange={(e)=>{
                        const next = { ...(addr||{street:'',number:'',district:'',city:'',state:'',cep:''}), number: e.target.value }
                        setAddr(next as Address)
                        setAddrErrors(validateAddr(next as Address))
                      }}
                    />
                    {addrErrors.number && <span className="text-xs text-red-600">{addrErrors.number}</span>}
                  </label>
                  <label>
                    Bairro
                    <input className="mt-1 w-full border rounded px-2 py-1" value={addr?.district || ''} onChange={(e)=>{
                      const next = { ...(addr||{street:'',number:'',district:'',city:'',state:'',cep:''}), district: e.target.value }
                      setAddr(next as Address)
                    }} />
                  </label>
                  <label>
                    Cidade
                    <input
                      className={`mt-1 w-full border rounded px-2 py-1 ${addrErrors.city ? 'border-red-500' : ''}`}
                      value={addr?.city || ''}
                      onChange={(e)=>{
                        const next = { ...(addr||{street:'',number:'',district:'',city:'',state:'',cep:''}), city: e.target.value }
                        setAddr(next as Address)
                        setAddrErrors(validateAddr(next as Address))
                      }}
                    />
                    {addrErrors.city && <span className="text-xs text-red-600">{addrErrors.city}</span>}
                  </label>
                  <label>
                    Estado
                    <input
                      className={`mt-1 w-full border rounded px-2 py-1 ${addrErrors.state ? 'border-red-500' : ''}`}
                      value={addr?.state || ''}
                      onChange={(e)=>{
                        const next = { ...(addr||{street:'',number:'',district:'',city:'',state:'',cep:''}), state: e.target.value.toUpperCase() }
                        setAddr(next as Address)
                        setAddrErrors(validateAddr(next as Address))
                      }}
                    />
                    {addrErrors.state && <span className="text-xs text-red-600">{addrErrors.state}</span>}
                  </label>
                  <label>
                    CEP
                    <input
                      className={`mt-1 w-full border rounded px-2 py-1 ${addrErrors.cep ? 'border-red-500' : ''}`}
                      value={addr?.cep || ''}
                      onChange={(e)=>{
                        const masked = formatCep(e.target.value)
                        const next = { ...(addr||{street:'',number:'',district:'',city:'',state:'',cep:''}), cep: masked }
                        setAddr(next as Address)
                        setAddrErrors(validateAddr(next as Address))
                      }}
                    />
                    {addrErrors.cep && <span className="text-xs text-red-600">{addrErrors.cep}</span>}
                  </label>
                </div>
                <div className="mt-2">
                  <button
                    className="text-sm px-3 py-1 rounded bg-gray-800 text-white hover:bg-gray-900 disabled:opacity-50"
                    disabled={busy || Object.keys(validateAddr(addr)).length > 0}
                    onClick={async ()=>{
                      try {
                        if (!addr) return
                        setBusy(true)
                        setError(null)
                        await setOrderAddress(orderId, addr)
                        const d = await getOrder(orderId)
                        setDetails(d)
                      } catch (e:any) {
                        setError(e?.message || 'Falha ao salvar endereço')
                      } finally {
                        setBusy(false)
                      }
                    }}
                  >
                    Salvar endereço
                  </button>
                </div>
              </section>
            )}
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
