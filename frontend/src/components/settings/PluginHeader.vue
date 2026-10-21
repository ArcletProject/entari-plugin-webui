<template>
  <div class="plugin-header">
    <div class="info">
      <h3>{{ plugin.name }}</h3>
      <div class="meta">
        <el-tag
          v-if="plugin.version"
          size="small"
        >
          v{{ plugin.version }}
        </el-tag>
        <span
          v-if="plugin.description"
          class="description"
        >{{ plugin.description }}</span>
      </div>
    </div>
    <div class="actions">
      <el-button
        size="small"
        type="primary"
        @click="emit('manage')"
      >
        管理
      </el-button>
      <el-button
        size="small"
        @click="emit('reload')"
      >
        重载
      </el-button>
      <el-button
        size="small"
        @click="emit('detail')"
      >
        详情
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PluginInfo } from "@/stores/settings";

defineProps<{ plugin: PluginInfo }>();
const emit = defineEmits<{
  manage: [];
  reload: [];
  detail: [];
}>();
</script>

<style scoped>
.plugin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
  margin-bottom: 16px;
}
.info {
  flex: 1;
  min-width: 0;
}
.info h3 {
  margin: 0 0 8px;
}
.meta {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.description {
  flex: 1;
  min-width: 0;
  white-space: normal;
  word-break: break-word;
}
.actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
</style>
