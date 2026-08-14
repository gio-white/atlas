import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const API = 'http://127.0.0.1:8000'
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
  '/export',
  '/import',
]

function proxy() {
  return {
    target: API,
    bypass(req: { headers: { accept?: string } }) {
      if (req.headers.accept?.includes('text/html')) return '/index.html'
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
