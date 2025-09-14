import React, { createContext, useContext, useEffect, useState } from 'react'
import type { UIConfig } from './schema'
import { defaultConfig } from './schema'

export const ConfigCtx = createContext<UIConfig>(defaultConfig)

export function useUIConfig(): UIConfig {
  return useContext(ConfigCtx)
}

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const [cfg, setCfg] = useState<UIConfig>(defaultConfig)

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const url = `${import.meta.env.BASE_URL || '/'}config.json`
        const res = await fetch(url, { cache: 'no-store' })
        if (alive && res.ok) {
          const ct = res.headers.get('Content-Type') || ''
          if (!ct.toLowerCase().includes('application/json')) {
            // Em dev, pode retornar index.html; ignora e usa default
            console.warn('ConfigProvider: /config.json não é JSON. Mantendo defaultConfig.')
            return
          }
          const data = (await res.json()) as UIConfig
          setCfg({
            ...defaultConfig,
            ...data,
            kanban: {
              columns: data?.kanban?.columns ?? defaultConfig.kanban.columns,
              actions: data?.kanban?.actions ?? defaultConfig.kanban.actions,
            },
          })
        }
      } catch {
        // fallback para defaultConfig em caso de erro
        console.warn('ConfigProvider: erro ao carregar /config.json, usando defaultConfig')
      }
    })()
    return () => {
      alive = false
    }
  }, [])

  return <ConfigCtx.Provider value={cfg}>{children}</ConfigCtx.Provider>
}
