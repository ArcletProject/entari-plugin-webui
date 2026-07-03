<template>
  <div class="market-page">
    <div class="toolbar">
      <el-input
        v-model="search"
        placeholder="搜索插件"
        style="width:240px"
        clearable
      />
      <el-select
        v-model="tag"
        placeholder="标签"
        clearable
        style="width:160px"
      >
        <el-option
          v-for="t in tags"
          :key="t"
          :label="t"
          :value="t"
        />
      </el-select>
      <el-tag
        v-if="fallback"
        type="warning"
      >
        本地缓存
      </el-tag>
    </div>
    <el-row :gutter="16">
      <el-col
        v-for="p in filtered"
        :key="p.name"
        :span="8"
        style="margin-bottom:16px"
      >
        <MarketCard
          :item="p"
          @install="startInstall(p)"
          @uninstall="startUninstall(p)"
        />
      </el-col>
    </el-row>
    <InstallProgress
      :task-id="taskId"
      @done="onDone"
    />
    <el-button
      v-if="taskFailed"
      size="small"
      style="margin-top:8px"
      @click="dismissError"
    >
      关闭
    </el-button>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import api from "@/api/client";
import MarketCard from "@/components/market/MarketCard.vue";
import InstallProgress from "@/components/market/InstallProgress.vue";

interface MarketPluginItem {
  name: string;
  description?: string;
  tags?: string[];
  homepage?: string;
  version?: string;
  authors?: string | string[];
  installed?: boolean;
  _installing?: boolean;
}

const list = ref<MarketPluginItem[]>([]);
const fallback = ref(false);
const search = ref("");
const tag = ref("");
const taskId = ref<string | undefined>(undefined);
const taskFailed = ref(false);

const tags = computed(() => {
  const s = new Set<string>();
  list.value.forEach((p) => (p.tags || []).forEach((t: string) => s.add(t)));
  return Array.from(s);
});
const filtered = computed(() => list.value.filter((p) => {
  const hitSearch = !search.value || p.name?.includes(search.value) || p.description?.includes(search.value);
  const hitTag = !tag.value || (p.tags || []).includes(tag.value);
  return hitSearch && hitTag;
}));

async function load() {
  const r = await api.get("/api/market/plugins");
  list.value = r.data.plugins || [];
  fallback.value = r.data.fallback || false;
}
async function startInstall(p: MarketPluginItem) {
  p._installing = true;
  taskFailed.value = false;
  try {
    const r = await api.post("/api/market/install", { name: p.name });
    taskId.value = r.data.task_id;
  } catch (e: unknown) { ElMessage.error((e as { message: string }).message); p._installing = false; }
}
async function startUninstall(p: MarketPluginItem) {
  try {
    const r = await api.post("/api/market/uninstall", { name: p.name });
    taskId.value = r.data.task_id;
  } catch (e: unknown) { ElMessage.error((e as { message: string }).message); }
}
function onDone(success: boolean) {
  if (success) {
    taskId.value = undefined;
    taskFailed.value = false;
    list.value.forEach((p) => delete p._installing);
    load();
  } else {
    taskFailed.value = true;
  }
}
function dismissError() {
  taskId.value = undefined;
  taskFailed.value = false;
  list.value.forEach((p) => delete p._installing);
}
onMounted(load);
</script>
<style scoped>
.market-page { padding: 16px; }
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; }
</style>
