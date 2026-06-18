import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Lets `npm run dev` (outside Docker) talk to a locally running backend
    // the same way the built nginx image proxies /api in production.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
