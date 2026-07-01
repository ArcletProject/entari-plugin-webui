import { ref, onUnmounted } from "vue";

export interface ChatMessage {
  id: string;
  role: "user" | "bot" | "system";
  content: string;
  time: Date;
}

function buildUrl() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${location.host}/api/chat`;
}

function uuid() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function useChat() {
  const connected = ref(false);
  const messages = ref<ChatMessage[]>([]);
  const error = ref<string>("");
  let ws: WebSocket | null = null;
  let reconnectTimer: number | null = null;
  let shouldReconnect = true;

  function connect() {
    if (!shouldReconnect) return;
    // 避免重复创建连接
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) return;

    ws = new WebSocket(buildUrl());
    ws.onopen = () => {
      connected.value = true;
      error.value = "";
      messages.value.push({ id: uuid(), role: "system", content: "已连接", time: new Date() });
    };
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        handleMessage(data);
      } catch {
        // ignore raw
      }
    };
    ws.onerror = () => {
      error.value = "连接错误";
    };
    ws.onclose = (ev) => {
      connected.value = false;
      const reason = ev.reason || `code ${ev.code}`;
      messages.value.push({ id: uuid(), role: "system", content: `连接已断开 (${reason})`, time: new Date() });
      if (shouldReconnect) {
        reconnectTimer = window.setTimeout(connect, 3000);
      }
    };
  }

  function handleMessage(data: any) {
    // 响应 adapter 的 API 调用（带 token）
    if (data.action && data.token) {
      ws?.send(JSON.stringify({ token: data.token, status: "ok", data: { id: uuid() } }));
      if (data.action === "message_create" && data.data?.content) {
        messages.value.push({ id: uuid(), role: "bot", content: data.data.content, time: new Date() });
      }
      return;
    }
    // 普通事件
    if (data.type === "message_create" && data.data?.message_content) {
      messages.value.push({
        id: data.data.message_id || uuid(),
        role: "user",
        content: data.data.message_content,
        time: new Date(),
      });
    }
  }

  function sendText(text: string) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const id = uuid();
    messages.value.push({ id, role: "user", content: text, time: new Date() });
    ws.send(
      JSON.stringify({
        type: "message_create",
        data: {
          user_id: "user",
          message_id: id,
          message_content: text,
        },
      }),
    );
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

  connect();
  onUnmounted(disconnect);

  return { connected, messages, error, sendText };
}
