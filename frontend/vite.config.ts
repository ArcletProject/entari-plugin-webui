import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  server: {
    proxy: {
      "/api": { target: "http://127.0.0.1:5150", changeOrigin: true },
      "/ws": { target: "ws://127.0.0.1:5150", ws: true },
    },
  },
  build: {
    outDir: "../src/entari_plugin_webui/static/frontend",
    emptyOutDir: true,
  },
});
