import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Send /api calls to FastAPI so the session cookie stays same-origin.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
