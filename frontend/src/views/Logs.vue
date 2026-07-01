<template>
  <div class="logs-page">
    <div class="toolbar">
      <el-tag :type="log.connected ? 'success' : 'danger'">{{ log.connected ? "已连接" : "未连接" }}</el-tag>
      <el-button @click="log.clear">清空</el-button>
    </div>
    <AnsiLogViewer :lines="log.lines" class="log-viewer" />
  </div>
</template>
<script setup lang="ts">
import { onMounted } from "vue";
import { useLogStore } from "@/stores/logs";
import AnsiLogViewer from "@/components/common/AnsiLogViewer.vue";

defineOptions({ name: "Logs" });

const log = useLogStore();

onMounted(() => {
  log.ensureConnection();
});
</script>
<style scoped>
.logs-page { display: flex; flex-direction: column; height: 100%; padding: 16px; }
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; }
.log-viewer { flex: 1; min-height: 0; border-radius: 8px; }
</style>
