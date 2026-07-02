<template>
  <el-card shadow="never" class="market-card">
    <template #header>
      <div class="card-header">
        <el-link v-if="item.homepage" :href="item.homepage" target="_blank" class="title-link">
          <span class="title">{{ item.name }}</span>
        </el-link>
        <span v-else class="title">{{ item.name }}</span>
      </div>
    </template>
    <div class="tags" v-if="item.tags?.length">
      <el-tag size="small" v-for="t in item.tags" :key="t">{{ t }}</el-tag>
    </div>
    <div class="desc">{{ item.description || "无描述" }}</div>
    <div class="meta">
      <span>版本: {{ item.version || "-" }}</span>
      <span>作者: {{ authors }}</span>
    </div>
    <div class="actions">
      <el-button size="small" @click="openHomepage" :disabled="!item.homepage">主页</el-button>
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
function openHomepage() {
  if (props.item.homepage) window.open(props.item.homepage, "_blank");
}
function install() { emit("install"); }
function uninstall() { emit("uninstall"); }
</script>
<style scoped>
.market-card { height: 100%; display: flex; flex-direction: column; background: var(--el-fill-color-light); border: none; }
:deep(.el-card__body) { flex: 1; display: flex; flex-direction: column; }
.card-header { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
.title { font-weight: bold; font-size: 16px; }
.title-link { text-decoration: none; }
.tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.desc { flex: 1; color: var(--el-text-color-primary); margin: 8px 0; }
.meta { font-size: 12px; color: var(--el-text-color-regular); margin-bottom: 12px; }
.meta span { margin-right: 12px; }
.actions { display: flex; gap: 8px; }
</style>
