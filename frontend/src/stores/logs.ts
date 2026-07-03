import { defineStore } from "pinia";
import { ref } from "vue";

function buildUrl(path: string) {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${location.host}${path}`;
}

export const useLogStore = defineStore("logs", () => {
  const connected = ref(false);
  const lines = ref<string[]>([]);
  const cap = 1000;
  let ws: WebSocket | null = null;
  let reconnectTimer: number | null = null;
  let shouldReconnect = true;

  function connect() {
    if (!shouldReconnect) return;
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) return;

    ws = new WebSocket(buildUrl("/ws/logs"));
    ws.onopen = () => {
      connected.value = true;
    };
    ws.onmessage = (ev) => {
      try {
        const m = JSON.parse(ev.data);
        if (m.type === "history" && Array.isArray(m.data)) {
          lines.value.push(...m.data);
        } else if (m.type === "log") {
          lines.value.push(String(m.data || ""));
        }
      } catch {
        lines.value.push(String(ev.data || ""));
      }
      if (lines.value.length > cap) lines.value = lines.value.slice(-cap);
    };
    ws.onerror = () => {};
    ws.onclose = () => {
      connected.value = false;
      if (shouldReconnect) {
        reconnectTimer = window.setTimeout(connect, 3000);
      }
    };
  }

  function ensureConnection() {
    connect();
  }

  function disconnect() {
    shouldReconnect = false;
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    ws?.close();
    ws = null;
  }

  function clear() {
    lines.value = [];
  }

  if (!ws && shouldReconnect) connect();

  return { connected, lines, ensureConnection, disconnect, clear };
});
