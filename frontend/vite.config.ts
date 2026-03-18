import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
      '/entities': 'http://localhost:8000',
      '/automations': 'http://localhost:8000',
      '/integrations': 'http://localhost:8000',
    },
  },
});
