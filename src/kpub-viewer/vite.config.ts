import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: './../../dist',
    chunkSizeWarningLimit: 1000,
    minify: false,
  },
  server: {
    proxy: {
      '/api/kpub': '/api/kpub', // No proxy, point to local server
      // '/api/kpub': 'http://localhost:5001', // Point to dev_server
    },
  },
})
