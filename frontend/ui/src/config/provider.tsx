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
        const res = await fetch('/config.json')
        if (alive && res.ok) {
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
        // fallback para defaultConfig
      }
    })()
    return () => {
      alive = false
    }
  }, [])

  return <ConfigCtx.Provider value={cfg}>{children}</ConfigCtx.Provider>
}
