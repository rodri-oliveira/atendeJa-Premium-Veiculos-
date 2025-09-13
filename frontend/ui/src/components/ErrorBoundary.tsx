import React from 'react'

type Props = { children: React.ReactNode }

type State = { hasError: boolean; errorId?: string; message?: string }

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(err: unknown): State {
    const errorId = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
    const message = err instanceof Error ? err.message : String(err)
    return { hasError: true, errorId, message }
  }

  componentDidCatch(error: unknown, info: React.ErrorInfo): void {
    // Log leve no console (sem vendor)
    // Em produção, isso pode ser enviado para a API de logs do backend se necessário
    // eslint-disable-next-line no-console
    console.error('[ui] boundary_error', { error, info, errorId: this.state.errorId })
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <div className="p-4 m-4 border rounded bg-red-50 text-red-800">
          <div className="font-semibold">Ocorreu um erro na interface</div>
          <div className="text-sm mt-1">Tente atualizar a página. Se o problema persistir, informe o suporte.</div>
          <div className="text-xs mt-2 text-red-600">ID do erro: {this.state.errorId}</div>
        </div>
      )
    }
    return this.props.children
  }
}
