<template>
  <div :class="['chat-message', data.role]">
    <template v-if="data.role === 'system'">
      <div class="system-bubble" v-html="renderedContent"></div>
    </template>
    <template v-else>
      <div class="avatar" :style="avatarStyle">{{ avatarText }}</div>
      <div class="body">
        <div class="meta">
          <span class="nickname">{{ nickname }}</span>
          <span class="time">{{ formatTime(data.time) }}</span>
        </div>
        <div class="bubble" v-html="renderedContent"></div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { renderPlainText } from "@/utils/html";
import { renderSatori } from "@/utils/satori";
import type { ChatMessage } from "@/stores/chat";

const props = defineProps<{ data: ChatMessage }>();

const avatarText = computed(() => {
  if (props.data.role === "bot") return "B";
  return "U";
});

const nickname = computed(() => {
  if (props.data.role === "bot") return "Bot";
  return "我";
});

const avatarStyle = computed(() => {
  const colors: Record<string, string> = {
    user: "var(--el-color-primary)",
    bot: "var(--el-color-success)",
  };
  return { backgroundColor: colors[props.data.role] || "var(--el-text-color-secondary)" };
});

// 用户消息按纯文本展示（escape + 换行）；bot 渲染 Satori elements；system 按纯文本处理
const renderedContent = computed(() => {
  if (props.data.role === "user") return renderPlainText(props.data.content);
  if (props.data.role === "system") return renderPlainText(props.data.content);
  return props.data.elements?.length ? renderSatori(props.data.elements) : renderPlainText(props.data.content);
});

function formatTime(d: Date) {
  return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.chat-message.user {
  flex-direction: row-reverse;
}
.chat-message.user .body {
  align-items: flex-end;
}
.chat-message.system {
  justify-content: center;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: bold;
  flex-shrink: 0;
  user-select: none;
}
.body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 80%;
}
.meta {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
}
.nickname {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
}
.time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.bubble {
  display: inline-block;
  padding: 10px 14px;
  border-radius: 12px;
  background: var(--el-bg-color);
  box-shadow: var(--el-box-shadow-light);
  word-break: break-word;
  line-height: 1.5;
}
.chat-message.user .bubble {
  background: var(--el-color-primary);
  color: #fff;
}
.system-bubble {
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
}
.bubble :deep(img) {
  max-width: 100%;
  border-radius: 8px;
}
.bubble :deep(.satori-quote) {
  margin: 0 0 8px;
  padding: 6px 10px;
  border-left: 3px solid var(--el-border-color);
  background: var(--el-fill-color);
  border-radius: 4px;
  opacity: 0.8;
}
.bubble :deep(.satori-at),
.bubble :deep(.satori-sharp) {
  color: var(--el-color-primary);
}
</style>
