import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // REST API — proxied to FastAPI
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        secure: false,
        // Also handle WebSocket upgrades on /api (e.g. /api/v1/call/ws)
        ws: true,
      },
      // Legacy WebSocket live alerts path
      '/ws': {
        target: 'ws://127.0.0.1:8001',
        changeOrigin: true,
        ws: true,
      }
    }
  }
})

