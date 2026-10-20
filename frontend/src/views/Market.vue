<template>
  <div
    v-loading="loading"
    class="market-page"
  >
    <el-card
      shadow="never"
      class="builtin-panel"
      :body-style="builtinBodyStyle"
    >
      <template #header>
        <div
          class="builtin-header"
          @click="builtinCollapsed = !builtinCollapsed"
        >
          <el-icon
            class="builtin-toggle"
            :class="{ expanded: !builtinCollapsed }"
          >
            <ArrowRight />
          </el-icon>
          <span class="builtin-title">内置插件</span>
          <span class="builtin-hint">随 entari 提供，可直接启用</span>
        </div>
      </template>
      <div>
        <div
          v-if="!filteredBuiltins.length"
          class="builtin-empty"
        >
          无匹配的内置插件
        </div>
        <div
          v-else
          class="builtin-list"
        >
          <div
            v-for="b in filteredBuiltins"
            :key="b.name"
            class="builtin-row"
          >
            <div class="builtin-info">
              <div class="builtin-name">
                {{ b.title }}
                <el-tag
                  size="small"
                  type="info"
                  effect="plain"
                >
                  {{ b.key }}
                </el-tag>
                <el-tag
                  v-if="b.static"
                  size="small"
                  type="warning"
                  effect="plain"
                >
                  常驻
                </el-tag>
              </div>
              <div class="builtin-desc">
                {{ b.description || "无描述" }}
              </div>
            </div>
            <el-switch
              :model-value="b.enabled"
              :loading="b._toggling"
              :disabled="b.static || b._toggling"
              @change="onToggle(b, $event)"
            />
          </div>
        </div>
      </div>
    </el-card>
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
import { ref, computed, onMounted, watch } from "vue";
import { ElMessage } from "element-plus";
import { ArrowRight } from "@element-plus/icons-vue";
import api from "@/api/client";
import MarketCard from "@/components/market/MarketCard.vue";
import InstallProgress from "@/components/market/InstallProgress.vue";

interface BuiltinItem {
  name: string;
  id: string;
  key: string;
  title: string;
  description?: string;
  loaded: boolean;
  enabled: boolean;
  static: boolean;
  _toggling?: boolean;
}

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

const loading = ref(false);
const list = ref<MarketPluginItem[]>([]);
const builtins = ref<BuiltinItem[]>([]);
const builtinCollapsed = ref(true);
const builtinBodyStyle = computed(() => (builtinCollapsed.value ? { display: "none" } : undefined));
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

const filteredBuiltins = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return builtins.value;
  return builtins.value.filter((b) =>
    b.title.toLowerCase().includes(q)
    || b.key.toLowerCase().includes(q)
    || (b.description || "").toLowerCase().includes(q),
  );
});

watch(search, (value) => {
  if (value.trim() && filteredBuiltins.value.length) builtinCollapsed.value = false;
});

async function load() {
  loading.value = true;
  try {
    const r = await api.get("/api/market/plugins");
    list.value = r.data.plugins || [];
    fallback.value = r.data.fallback || false;
  } finally {
    loading.value = false;
  }
}
async function loadBuiltins() {
  try {
    const r = await api.get("/api/market/builtins");
    builtins.value = r.data.data || [];
  } catch (e: unknown) {
    ElMessage.error((e as { message: string }).message);
  }
}
function onToggle(b: BuiltinItem, value: string | number | boolean) {
  toggleBuiltin(b, Boolean(value));
}
async function toggleBuiltin(b: BuiltinItem, enable: boolean) {
  b._toggling = true;
  try {
    await api.post(`/api/market/builtins/${encodeURIComponent(b.name)}/toggle`, { enable });
    b.enabled = enable;
    b.loaded = enable;
    ElMessage.success(enable ? `已启用 ${b.title}` : `已禁用 ${b.title}`);
  } catch (e: unknown) {
    ElMessage.error((e as { message: string }).message);
    await loadBuiltins();
  } finally {
    b._toggling = false;
  }
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
onMounted(() => {
  load();
  loadBuiltins();
});
</script>
<style scoped>
.market-page { padding: 16px; min-height: 300px; }
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; }
.builtin-panel { margin-bottom: 16px; background: var(--el-fill-color-light); border: none; }
.builtin-header { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.builtin-toggle { transition: transform 0.2s; }
.builtin-toggle.expanded { transform: rotate(90deg); }
.builtin-title { font-weight: bold; font-size: 16px; }
.builtin-hint { font-size: 12px; color: var(--el-text-color-secondary); }
.builtin-list { display: flex; flex-direction: column; }
.builtin-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.builtin-row:last-child { border-bottom: none; }
.builtin-info { flex: 1; min-width: 0; }
.builtin-name { display: flex; align-items: center; gap: 8px; font-weight: 500; }
.builtin-desc { margin-top: 4px; font-size: 12px; color: var(--el-text-color-regular); }
.builtin-empty { color: var(--el-text-color-secondary); font-size: 12px; }
</style>
