import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// `npm run dev` (outside Docker) proxies /api to a backend so the SPA works the
// same way the built nginx image does in production. Defaults to a local
// backend; set VITE_PROXY_TARGET to point at a deployed backend instead, e.g.
//   VITE_PROXY_TARGET=https://gastrosense-backend.onrender.com npm run dev
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
