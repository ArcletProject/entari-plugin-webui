<template>
  <div class="logs-page">
    <div class="toolbar">
      <el-tag :type="connected ? 'success' : 'danger'">{{ connected ? "已连接" : "未连接" }}</el-tag>
      <el-button @click="clear">清空</el-button>
    </div>
    <AnsiLogViewer :lines="lines" class="log-viewer" />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { useWebSocketConnection } from "@/composables/useWebSocket";
import AnsiLogViewer from "@/components/common/AnsiLogViewer.vue";

const lines = ref<string[]>([]);
const cap = 1000;
const { connected } = useWebSocketConnection("/ws/logs", {
  onMessage: (m) => {
    if (m.type === "history" && Array.isArray(m.data)) {
      lines.value.push(...m.data);
    } else if (m.type === "log") {
      lines.value.push(String(m.data || ""));
    }
    if (lines.value.length > cap) lines.value = lines.value.slice(-cap);
  },
});
function clear() { lines.value = []; }
</script>
<style scoped>
.logs-page { display: flex; flex-direction: column; height: 100%; padding: 16px; }
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; }
.log-viewer { flex: 1; min-height: 0; border-radius: 8px; }
</style>
