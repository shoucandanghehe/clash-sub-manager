import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import vuetify from 'vite-plugin-vuetify'

export default defineConfig({
  base: '/ui/',
  plugins: [vue(), vuetify({ autoImport: true })],
  server: {
    proxy: {
      '^/(api/v1|subscriptions|templates|template-patches|composite-templates|rule-sources|merge-profiles|convert|merge)(/|$)': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
