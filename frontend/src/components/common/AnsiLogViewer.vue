<template>
  <div class="ansi-log" ref="host">
    <div v-for="(line, i) in lines" :key="i" v-html="render(line)"></div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import AnsiToHtml from "ansi-to-html";
const props = defineProps<{ lines: string[] }>();
const host = ref<HTMLElement>();
const converter = new AnsiToHtml({ newline: true });
function render(line: string) { return converter.toHtml(line); }
watch(() => props.lines.length, async () => {
  await nextTick();
  if (host.value) host.value.scrollTop = host.value.scrollHeight;
});
</script>
<style scoped>
.ansi-log {
  height: 100%;
  overflow: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  font-family: var(--el-font-family-monospace, monospace);
  font-size: 13px;
  white-space: pre-wrap;
}
</style>
