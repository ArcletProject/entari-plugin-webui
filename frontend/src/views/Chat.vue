<template>
  <div class="chat-page">
    <div class="chat-header">
      <h3>{{ t("menu.chat") }}</h3>
      <el-tag :type="connected ? 'success' : 'danger'" size="small">
        {{ connected ? "已连接" : "未连接" }}
      </el-tag>
    </div>
    <div class="chat-messages" ref="msgHost">
      <div
        v-for="m in messages"
        :key="m.id"
        :class="['message-row', m.role]"
      >
        <div class="bubble">
          <div class="content">{{ m.content }}</div>
          <div class="time">{{ formatTime(m.time) }}</div>
        </div>
      </div>
    </div>
    <div class="chat-input">
      <el-input
        v-model="input"
        placeholder="输入消息..."
        :disabled="!connected"
        @keyup.enter="send"
      />
      <el-button type="primary" :disabled="!connected || !input.trim()" @click="send">
        发送
      </el-button>
    </div>
    <el-alert v-if="error" :title="error" type="error" :closable="false" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { useI18n } from "vue-i18n";
import { useChat } from "@/composables/useChat";

const { t } = useI18n();
const { connected, messages, error, sendText } = useChat();
const input = ref("");
const msgHost = ref<HTMLElement>();

function send() {
  const text = input.value.trim();
  if (!text) return;
  sendText(text);
  input.value = "";
}

function formatTime(d: Date) {
  return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

watch(
  () => messages.value.length,
  async () => {
    await nextTick();
    if (msgHost.value) msgHost.value.scrollTop = msgHost.value.scrollHeight;
  },
);
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
}
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.chat-header h3 {
  margin: 0;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 12px;
  background: var(--el-fill-color-light);
  margin-bottom: 12px;
}
.message-row {
  display: flex;
  margin-bottom: 12px;
}
.message-row.user {
  justify-content: flex-end;
}
.message-row.bot {
  justify-content: flex-start;
}
.message-row.system {
  justify-content: center;
}
.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  background: var(--el-bg-color);
  box-shadow: var(--el-box-shadow-light);
}
.message-row.user .bubble {
  background: var(--el-color-primary);
  color: #fff;
}
.message-row.system .bubble {
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  font-size: 12px;
  padding: 4px 10px;
}
.content {
  word-break: break-word;
  white-space: pre-wrap;
}
.time {
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.7;
  text-align: right;
}
.chat-input {
  display: flex;
  gap: 8px;
}
</style>
