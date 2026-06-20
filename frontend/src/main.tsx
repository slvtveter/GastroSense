import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'

// A GitHub Actions cron (.github/workflows/keepalive.yml) pings the services
// every 10 min so the free-tier backend normally never sleeps. This retry
// budget is the safety net for the rare cold start that slips through (e.g.
// the keepalive lapses): waking the free backend has been observed to take
// several MINUTES, during which every API call 502s. ~24 retries with a 10s
// cap span roughly 4 min, so the dashboard waits the backend out instead of
// giving up after a few seconds and showing a stuck/empty screen.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 24,
      retryDelay: (attempt) => Math.min(2000 * (attempt + 1), 10000),
      refetchOnWindowFocus: false,
    },
    // Mutations (chat, seed-demo, upload) default to zero retries in React
    // Query, unlike queries above - so a chat message sent while the backend
    // is still waking up failed instantly with a raw 502 and never retried.
    mutations: {
      retry: 12,
      retryDelay: (attempt) => Math.min(2000 * (attempt + 1), 10000),
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
