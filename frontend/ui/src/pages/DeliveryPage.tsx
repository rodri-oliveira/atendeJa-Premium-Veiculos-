import React from 'react'

export default function DeliveryPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl md:text-2xl font-bold">Entregas</h1>
        <p className="text-sm text-gray-600">Visão inicial. Em breve listaremos entregas ativas e histórico.</p>
      </header>

      <section className="bg-white border rounded p-4">
        <h2 className="font-semibold mb-2">Em breve</h2>
        <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
          <li>Lista de entregas em rota com status e tempo em trânsito.</li>
          <li>Filtros por entregador, status e período.</li>
          <li>Histórico de entregas finalizadas e reentregas.</li>
        </ul>
      </section>
    </div>
  )
}
