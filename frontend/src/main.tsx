import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'

// The backend is a free-tier service that can take ~50s to cold-start. Retry
// generously with a long backoff so the very first requests survive that wake
// window instead of erroring out and leaving the dashboard stuck.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 12,
      retryDelay: (attempt) => Math.min(2000 * (attempt + 1), 10000),
      refetchOnWindowFocus: false,
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
