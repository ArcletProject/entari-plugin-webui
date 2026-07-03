<template>
  <div class="chat-page">
    <div class="chat-header">
      <h3>{{ t("menu.chat") }}</h3>
      <el-tag
        :type="chat.connected ? 'success' : 'danger'"
        size="small"
      >
        {{ chat.connected ? t("chat.connected") : t("chat.disconnected") }}
      </el-tag>
    </div>

    <div
      ref="msgHost"
      class="chat-messages"
    >
      <el-empty
        v-if="!chat.messages.length"
        :description="t('chat.empty')"
      />
      <template v-else>
        <ChatMessage
          v-for="m in chat.messages"
          :key="m.id"
          :data="m"
        />
      </template>
    </div>

    <div class="chat-footer">
      <div
        v-if="quote"
        class="quote-bar"
      >
        <span>{{ t("chat.replyTo") }} {{ quote.content.slice(0, 30) }}</span>
        <el-icon
          class="close"
          @click="quote = null"
        >
          <Close />
        </el-icon>
      </div>
      <div class="chat-input">
        <el-input
          v-model="input"
          type="textarea"
          :rows="1"
          :autosize="{ minRows: 1, maxRows: 6 }"
          resize="none"
          :placeholder="t('chat.placeholder')"
          :disabled="!chat.connected"
          @keydown="onKeydown"
        />
        <el-button
          type="primary"
          :disabled="!chat.connected || !input.trim()"
          @click="send"
        >
          {{ t("chat.send") }}
        </el-button>
      </div>
    </div>

    <el-alert
      v-if="chat.error"
      :title="chat.error"
      type="error"
      :closable="false"
      class="chat-error"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { Close } from "@element-plus/icons-vue";
import { useChatStore, type ChatMessage as ChatMessageData } from "@/stores/chat";
import ChatMessage from "@/components/chat/ChatMessage.vue";

defineOptions({ name: "Chat" });

const { t } = useI18n();
const chat = useChatStore();
const input = ref("");
const msgHost = ref<HTMLElement>();
const quote = ref<ChatMessageData | null>(null);

onMounted(() => {
  chat.ensureConnection();
});

function send() {
  const text = input.value.trim();
  if (!text) return;
  chat.sendText(text);
  input.value = "";
  quote.value = null;
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

watch(
  () => chat.messages.length,
  async () => {
    await nextTick();
    if (msgHost.value) {
      msgHost.value.scrollTo({ top: msgHost.value.scrollHeight, behavior: "smooth" });
    }
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
.chat-footer {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 12px;
  background: var(--el-bg-color);
}
.quote-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  background: var(--el-fill-color);
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.quote-bar .close {
  cursor: pointer;
}
.chat-input {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.chat-input .el-textarea {
  flex: 1;
}
.chat-error {
  margin-top: 12px;
}
</style>
