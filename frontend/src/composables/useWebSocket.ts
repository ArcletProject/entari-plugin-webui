import { ref, onUnmounted } from "vue";

export function useWebSocketConnection(path: string, opts: { onMessage: (m: any) => void; onError?: () => void; autoReconnect?: boolean } = { onMessage: () => {} }) {
  const connected = ref(false);
  let ws: WebSocket | null = null;
  let reconnectTimer: number | null = null;
  const auto = opts.autoReconnect ?? true;

  function buildUrl() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${location.host}${path}`;
  }

  function connect() {
    ws = new WebSocket(buildUrl());
    ws.onopen = () => { connected.value = true; };
    ws.onmessage = (ev) => {
      try { opts.onMessage(JSON.parse(ev.data)); }
      catch { opts.onMessage({ type: "raw", data: ev.data }); }
    };
    ws.onerror = () => { opts.onError?.(); };
    ws.onclose = () => {
      connected.value = false;
      if (auto) reconnectTimer = window.setTimeout(connect, 3000);
    };
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    ws?.close();
  }

  connect();
  onUnmounted(disconnect);
  return { connected, disconnect };
}
