import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  base: '/static/',
  build: {
    manifest: true,
    emptyOutDir: true,
    outDir: resolve(__dirname, 'static/dist'),
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'frontend/main.js'),
        style: resolve(__dirname, 'frontend/style.css'),
      },
      output: {
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith('.css')) {
            return 'style.css';
          }
          return 'assets/[name]-[hash][extname]';
        },
      },
    },
  },
  server: {
    origin: 'http://localhost:5173',
  },
});
