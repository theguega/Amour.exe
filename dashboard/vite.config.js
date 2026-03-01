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
        secure: true, // Use secure: true for production APIs
        rewrite: (path) => path.replace(/^\/weave-api/, ''),
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('[proxy error]', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            // Ensure the host header is set correctly for HTTPS targets
            proxyReq.setHeader('host', 'trace.wandb.ai');
            // console.log('[proxy req]', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            // console.log('[proxy res]', proxyRes.statusCode, req.url);
          });
        },
      }
    }
  }
})
