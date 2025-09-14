export type ColumnSpec = {
  status: string
  title: string
}

export type ActionSpec = {
  label: string
  next: string
}

export type Branding = {
  appTitle?: string
}

export type UIConfig = {
  branding?: Branding
  kanban: {
    columns: ColumnSpec[]
    actions?: Record<string, ActionSpec[]>
  }
  ui?: {
    compactDefault?: boolean
    zoomDefault?: number
    columnWidth?: number
    targetColumnsDefault?: number
    columnWidthMin?: number
    columnWidthMax?: number
  }
}

export const defaultConfig: UIConfig = {
  branding: { appTitle: 'Painel Operacional' },
  kanban: {
    columns: [
      { status: 'draft', title: 'Rascunho' },
      { status: 'pending_payment', title: 'Aguardando pagamento' },
      { status: 'paid', title: 'Pago' },
      { status: 'in_kitchen', title: 'Em preparo' },
      { status: 'out_for_delivery', title: 'Saiu para entrega' },
      { status: 'delivered', title: 'Entregue' },
      { status: 'canceled', title: 'Cancelado' },
    ],
    actions: {
      draft: [
        { label: 'Cancelar', next: 'canceled' },
      ],
      paid: [
        { label: 'Marcar em preparo', next: 'in_kitchen' },
      ],
      in_kitchen: [
        { label: 'Saiu p/ entrega', next: 'out_for_delivery' },
      ],
      out_for_delivery: [
        { label: 'Finalizar', next: 'delivered' },
      ],
    },
  },
  ui: {
    compactDefault: false,
    zoomDefault: 1,
    columnWidth: 280,
    targetColumnsDefault: 7,
    columnWidthMin: 220,
    columnWidthMax: 320,
  },
}
