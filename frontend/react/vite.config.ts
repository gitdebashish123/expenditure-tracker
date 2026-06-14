import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import path from "path";

export default defineConfig({
  plugins: [
    react(),

    // PWA — makes Wallet Mantra installable on iPhone/Android home screen
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.ico", "icons/*.png"],
      manifest: {
        name:             "Wallet Mantra",
        short_name:       "WalletMantra",
        description:      "Beyond expense tracking",
        theme_color:      "#0a0a0f",
        background_color: "#0a0a0f",
        display:          "standalone",
        orientation:      "portrait",
        start_url:        "/",
        icons: [
          {
            src:   "/icons/icon-192.png",
            sizes: "192x192",
            type:  "image/png",
          },
          {
            src:   "/icons/icon-512.png",
            sizes: "512x512",
            type:  "image/png",
          },
          {
            src:     "/icons/icon-512.png",
            sizes:   "512x512",
            type:    "image/png",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        // Cache all static assets in the build
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"],
        runtimeCaching: [
          {
            // Summary + balance — serve from cache, update in background
            // Means last balance is visible even on poor connection
            urlPattern: /\/summary\/.*/,
            handler:    "NetworkFirst",
            options: {
              cacheName:  "api-summary",
              expiration: { maxEntries: 12 },
            },
          },
          {
            // Expense lists — stale OK for offline reading
            urlPattern: /\/expenses\/.*/,
            handler:    "StaleWhileRevalidate",
            options: {
              cacheName:  "api-expenses",
              expiration: { maxEntries: 24 },
            },
          },
        ],
      },
    }),
  ],

  resolve: {
    alias: {
      // @ maps to src/ — used throughout as @/components, @/utils etc.
      "@": path.resolve(__dirname, "./src"),
    },
  },

  server: {
    port: 5173,
    // Proxy not needed — CORS handled in FastAPI backend
    // Both Streamlit (:8501) and React (:5173) talk directly to :8000
  },
});
