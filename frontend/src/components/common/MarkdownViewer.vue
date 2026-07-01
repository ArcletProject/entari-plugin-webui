<template>
  <div class="markdown-viewer" v-html="html"></div>
</template>
<script setup lang="ts">
import { computed } from "vue";
import { marked } from "marked";
const props = defineProps<{ source?: string }>();
const html = computed(() => marked.parse(props.source || "", { async: false }) as string);
</script>
<style scoped>
.markdown-viewer {
  line-height: 1.6;
  color: var(--el-text-color-regular);
}
.markdown-viewer :deep(h1),
.markdown-viewer :deep(h2),
.markdown-viewer :deep(h3),
.markdown-viewer :deep(h4) {
  margin-top: 16px;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}
.markdown-viewer :deep(p) {
  margin: 8px 0;
}
.markdown-viewer :deep(code) {
  background: var(--el-fill-color);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--el-font-family-monospace, monospace);
}
.markdown-viewer :deep(pre) {
  background: var(--el-fill-color);
  padding: 12px;
  border-radius: 8px;
  overflow: auto;
}
.markdown-viewer :deep(pre code) {
  background: transparent;
  padding: 0;
}
.markdown-viewer :deep(ul),
.markdown-viewer :deep(ol) {
  padding-left: 20px;
}
.markdown-viewer :deep(a) {
  color: var(--el-color-primary);
}
.markdown-viewer :deep(blockquote) {
  margin: 8px 0;
  padding-left: 12px;
  border-left: 4px solid var(--el-border-color);
  color: var(--el-text-color-secondary);
}
</style>
