// ------------------------------------------------------------------
// File: frontend/vite.config.ts
// Purpose: Configures the Vite dev server and build with the React plugin.
// ------------------------------------------------------------------

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Enable React support in Vite.
// ref: https://vite.dev/guide/
export default defineConfig({
  plugins: [react()],
})
