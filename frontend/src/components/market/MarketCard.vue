<template>
  <el-card shadow="hover" class="market-card">
    <template #header>
      <div class="card-header">
        <span class="title">{{ item.name }}</span>
        <el-tag size="small" v-for="t in item.tags" :key="t" style="margin-left:4px">{{ t }}</el-tag>
      </div>
    </template>
    <div class="desc">{{ item.description || "无描述" }}</div>
    <div class="meta">
      <span>版本: {{ item.version || "-" }}</span>
      <span>作者: {{ authors }}</span>
    </div>
    <div class="actions">
      <el-button type="primary" size="small" :loading="installing" :disabled="item.installed" @click="install">{{ item.installed ? "已安装" : "安装" }}</el-button>
      <el-button size="small" :disabled="!item.installed" @click="uninstall">卸载</el-button>
    </div>
  </el-card>
</template>
<script setup lang="ts">
import { computed } from "vue";
const props = defineProps<{ item: any }>();
const emit = defineEmits<{ install: []; uninstall: [] }>();
const installing = computed(() => props.item._installing);
const authors = computed(() => {
  const a = props.item.authors;
  if (!a) return "-";
  return Array.isArray(a) ? a.join(", ") : String(a);
});
function install() { emit("install"); }
function uninstall() { emit("uninstall"); }
</script>
<style scoped>
.market-card { height: 100%; display: flex; flex-direction: column; }
.card-header { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
.title { font-weight: bold; font-size: 16px; }
.desc { flex: 1; color: var(--el-text-color-secondary); margin: 8px 0; }
.meta { font-size: 12px; color: var(--el-text-color-secondary); margin-bottom: 12px; }
.meta span { margin-right: 12px; }
.actions { display: flex; gap: 8px; }
</style>
