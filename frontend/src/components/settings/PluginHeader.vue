<template>
  <div class="plugin-header">
    <div class="info">
      <h3>{{ plugin.name }}</h3>
      <div class="meta">
        <el-tag size="small" v-if="plugin.version">v{{ plugin.version }}</el-tag>
        <span v-if="plugin.description" class="description">{{ plugin.description }}</span>

      </div>
    </div>
    <div class="actions">
      <el-switch
        :model-value="plugin.enabled"
        :disabled="plugin.is_static"
        @change="(v: any) => emit('toggle', v)"
      />
      <el-button size="small" @click="emit('reload')">重载</el-button>
      <el-button size="small" @click="emit('detail')">详情</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PluginInfo } from "@/stores/settings";

defineProps<{ plugin: PluginInfo }>();
const emit = defineEmits<{
  toggle: [value: boolean];
  reload: [];
  detail: [];
}>();
</script>

<style scoped>
.plugin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
  margin-bottom: 16px;
}
.info h3 {
  margin: 0 0 8px;
}
.meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.description {
  white-space: normal;
  word-break: break-word;
  flex: 1;
}
.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
