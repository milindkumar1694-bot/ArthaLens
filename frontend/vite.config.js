import { defineConfig } from 'vite';

export default defineConfig({
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify(process.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1')
  },
  build: {
    target: 'esnext',
    outDir: 'dist'
  }
});
