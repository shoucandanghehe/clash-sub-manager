import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import vuetify from 'vite-plugin-vuetify'

export default defineConfig({
  base: '/ui/',
  plugins: [vue(), vuetify({ autoImport: true })],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
