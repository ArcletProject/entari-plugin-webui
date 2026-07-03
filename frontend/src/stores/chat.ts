import { defineStore } from "pinia";
import { ref } from "vue";
import { buildTextElement, type SatoriElement } from "@/utils/satori";

export interface ChatMessage {
  id: string;
  role: "user" | "bot" | "system";
  content: string;
  elements?: SatoriElement[];
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

function elementsToText(elements: SatoriElement[] | undefined): string {
  if (!elements) return "";
  return elements
    .map((el) => {
      if (el.type === "text") return String(el.attrs?.text ?? "");
      if (el.type === "img" || el.type === "image") return "[图片]";
      if (el.type === "at") return `@${el.attrs?.name ?? el.attrs?.id ?? ""}`;
      if (el.children) return elementsToText(el.children);
      return "";
    })
    .join("");
}

export const useChatStore = defineStore("chat", () => {
  const connected = ref(false);
  const messages = ref<ChatMessage[]>([]);
  const error = ref<string>("");
  let ws: WebSocket | null = null;
  let reconnectTimer: number | null = null;
  let shouldReconnect = true;

  function connect() {
    if (!shouldReconnect) return;
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

  function handleMessage(data: Record<string, unknown>) {
    // 响应 adapter 的 API 调用（带 token）
    if (data.action && data.token) {
      ws?.send(JSON.stringify({ token: data.token, status: "ok", data: { id: uuid() } }));
      if (data.action === "message_create") {
        const elements: SatoriElement[] | undefined = data.data?.elements;
        const content = elementsToText(elements);
        messages.value.push({ id: uuid(), role: "bot", content, elements, time: new Date() });
      }
      return;
    }
    // 普通事件：用户消息回显
    if (data.type === "message_create") {
      const elements: SatoriElement[] | undefined = data.data?.elements;
      const content = elementsToText(elements);
      messages.value.push({
        id: data.data?.message_id || uuid(),
        role: "user",
        content,
        elements,
        time: new Date(),
      });
    }
  }

  function sendText(text: string, peerType: "user" | "channel" = "user", peerId = "") {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const id = uuid();
    const elements = [buildTextElement(text)];
    messages.value.push({ id, role: "user", content: text, elements, time: new Date() });
    ws.send(
      JSON.stringify({
        type: "message_create",
        data: {
          peer_type: peerType,
          peer_id: peerId,
          message_id: id,
          elements,
        },
      }),
    );
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

  // 页面加载后自动连接一次
  if (!ws && shouldReconnect) connect();

  return {
    connected,
    messages,
    error,
    sendText,
    ensureConnection,
    disconnect,
  };
});
