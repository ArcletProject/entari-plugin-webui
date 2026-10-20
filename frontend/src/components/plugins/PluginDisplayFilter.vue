<template>
  <div class="plugin-display-filter">
    <el-segmented
      :model-value="modelValue"
      :options="options"
      size="small"
      @update:model-value="onChange"
    />
  </div>
</template>

<script setup lang="ts">
import type { PluginDisplayMode } from "@/utils/plugin-tree";

defineProps<{ modelValue: PluginDisplayMode }>();
const emit = defineEmits<{ "update:modelValue": [value: PluginDisplayMode] }>();

const options = [
  { label: "仅顶层", value: "top" },
  { label: "有元数据/配置", value: "configured" },
  { label: "全部", value: "all" },
];

function onChange(value: string | number | boolean) {
  emit("update:modelValue", value as PluginDisplayMode);
}
</script>

<style scoped>
.plugin-display-filter {
  max-width: 100%;
  overflow-x: auto;
  padding-bottom: 2px;
}
.plugin-display-filter :deep(.el-segmented) {
  white-space: nowrap;
}
</style>
