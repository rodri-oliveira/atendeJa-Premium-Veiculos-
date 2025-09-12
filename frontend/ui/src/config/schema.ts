export type ColumnSpec = {
  status: string
  title: string
}

export type Branding = {
  appTitle?: string
}

export type UIConfig = {
  branding?: Branding
  kanban: {
    columns: ColumnSpec[]
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
  },
}
