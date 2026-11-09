import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Tunnel cloudflared per far vedere il sito fuori dalla rete locale
    // (cloudflared tunnel --url http://localhost:5173).
    allowedHosts: [".trycloudflare.com"],
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
      },
    },
  },
});
