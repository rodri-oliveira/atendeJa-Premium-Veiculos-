import matchers from '@testing-library/jest-dom/matchers'
import { expect } from 'vitest'
expect.extend(matchers)
// Define ENV used by the frontend at runtime (não substituir o objeto window do jsdom)
if (typeof (globalThis as any).window !== 'undefined') {
  ;(globalThis as any).window.ENV = (globalThis as any).window.ENV || { API_BASE_URL: 'http://api:8000' }
}

// React DOM checks `document.activeElement instanceof HTMLIFrameElement` in some paths.
// jsdom may not define HTMLIFrameElement, causing "Right-hand side of 'instanceof' is not an object".
// Provide a minimal stub for tests.
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
const IFrameCtor = (globalThis as any).HTMLIFrameElement || function HTMLIFrameElement() {}
;(globalThis as any).HTMLIFrameElement = IFrameCtor
;(globalThis as any).window.HTMLIFrameElement = IFrameCtor

// Stubs de seleção para o React DOM sob jsdom
try {
  if (typeof document !== 'undefined') {
    if (!(document as any).hasFocus) {
      ;(document as any).hasFocus = () => true
    }
    const body = document.body || document.createElement('body')
    const desc = Object.getOwnPropertyDescriptor(document, 'activeElement')
    if (!desc || typeof desc.get !== 'function') {
      Object.defineProperty(document, 'activeElement', {
        configurable: true,
        get: () => body,
      })
    }
  }
} catch {}

// Ensure selection-related APIs exist to avoid React DOM instanceof/selection errors
try {
  if (!(document as any).hasFocus) {
    ;(document as any).hasFocus = () => true
  }
  const body = document.body || document.createElement('body')
  if (Object.getOwnPropertyDescriptor(document, 'activeElement')?.get == null) {
    Object.defineProperty(document, 'activeElement', {
      configurable: true,
      get: () => body,
    })
  }
} catch {}
