import type { IncomingMessage, ServerResponse } from 'node:http'
import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const API = 'http://127.0.0.1:8000'
const API_UNREACHABLE = 'API is not reachable. Start it with atlas serve.'
const apiPrefixes = [
  '/areas',
  '/metrics',
  '/habits',
  '/goals',
  '/entries',
  '/views',
  '/screen',
  '/updates',
  '/slips',
  '/tasks',
  '/journal',
  '/entertainment',
  '/export',
  '/import',
]

function headerValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value.join(',')
  return value ?? ''
}

function isDocumentRequest(req: IncomingMessage): boolean {
  const dest = headerValue(req.headers['sec-fetch-dest'])
  const accept = headerValue(req.headers.accept)
  return dest === 'document' || accept.includes('text/html')
}

function isServerResponse(res: unknown): res is ServerResponse {
  return typeof res === 'object' && res !== null && 'writeHead' in res
}

function proxy() {
  return {
    target: API,
    bypass(req: IncomingMessage) {
      if (isDocumentRequest(req)) return '/index.html'
    },
    configure(proxyServer: {
      on: (event: 'error', listener: (...args: unknown[]) => void) => void
    }) {
      proxyServer.on('error', (_err: unknown, _req: unknown, res: unknown) => {
        if (isServerResponse(res) && !res.headersSent) {
          res.writeHead(502, { 'content-type': 'application/json' })
          res.end(JSON.stringify({ detail: API_UNREACHABLE }))
        }
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: Object.fromEntries(apiPrefixes.map((prefix) => [prefix, proxy()])),
  },
  test: {
    environment: 'node',
  },
})
