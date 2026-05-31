import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// PWA is added in T2.9 — placeholder import kept for reference
// import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    // VitePWA added in T2.9
  ],
  resolve: {
    alias: {
      // @ maps to src/ — used throughout the codebase as @/components, @/utils etc.
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    // Proxy not needed — CORS is handled in FastAPI backend
    // Both Streamlit (:8501) and React (:5173) talk directly to backend (:8000)
  },
});
