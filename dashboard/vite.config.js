import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/weave-api': {
        target: 'https://trace.wandb.ai',
        changeOrigin: true,
        secure: false, // Troubleshooting 502: disable SSL verification temporarily
        rewrite: (path) => path.replace(/^\/weave-api/, ''),
      }
    }
  }
})
