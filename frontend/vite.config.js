import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development the Vite server proxies /api to Flask, so the browser sees a
// single origin (no CORS issues). In Docker, nginx does the same job.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': process.env.VITE_API_PROXY || 'http://localhost:5000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    css: false,
  },
})
