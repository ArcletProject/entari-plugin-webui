# Phase 12: Settings Page Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge the existing `/config` and `/plugins` pages into a single `/settings` page with an expanded sidebar, plugin header metadata/actions, and special metadata rendering outside the regular config form.

**Architecture:** A new `Settings.vue` view coordinates a `settings` Pinia store, a `SettingsSidebar` for navigation, a `PluginHeader` for plugin actions/metadata, and a `MetaSettings` component for `$`-prefixed metadata. Regular config data flows through `DualConfigEditor` as before. Old routes redirect to `/settings`.

**Tech Stack:** Vue 3.5, Element Plus, Pinia, Vue Router, TypeScript.

---

## File Map

| File | Responsibility |
|------|----------------|
| `frontend/src/stores/settings.ts` | Global state: plugin list, current section, schema/data split into meta/config, dirty/save flags. |
| `frontend/src/components/settings/SettingsSidebar.vue` | Left sidebar: search, three always-expanded groups, section selection. |
| `frontend/src/components/settings/PluginHeader.vue` | Top card for plugins: name, description, version, toggle, reload, details. |
| `frontend/src/components/settings/MetaSettings.vue` | Render `metaSchema`/`metaData` as a visually distinct card. |
| `frontend/src/views/Settings.vue` | Compose sidebar, header, meta settings, and config form. |
| `frontend/src/router/index.ts` | Add `/settings`, redirect `/config` and `/plugins`. |
| `frontend/src/stores/menu.ts` | Replace `config`/`plugins` menu items with single `settings` item. |
| `src/entari_plugin_webui/api/menus.py` | Update backend builtin menus. |
| `frontend/src/i18n/zh-CN.ts` | Add `menu.settings`. |
| `frontend/src/views/Dashboard.vue` | Update button links to `/settings`. |
| `frontend/src/views/Config.vue` | Delete or replace with redirect. |
| `frontend/src/views/Plugins.vue` | Delete or replace with redirect. |

---

### Task 1: Update Router and Menu

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/stores/menu.ts`
- Modify: `src/entari_plugin_webui/api/menus.py`
- Modify: `frontend/src/i18n/zh-CN.ts`

- [ ] **Step 1: Update `frontend/src/router/index.ts`**

Add `/settings` route and redirects. Replace the existing routes block with:

```ts
const routes: RouteRecordRaw[] = [
  { path: "/", component: () => import("@/views/Dashboard.vue"), meta: { layout: "default" } },
  { path: "/login", component: () => import("@/views/Login.vue"), meta: { layout: "blank" } },
  { path: "/settings", component: () => import("@/views/Settings.vue"), meta: { layout: "default", label_key: "menu.settings" } },
  { path: "/config", redirect: "/settings" },
  { path: "/plugins", redirect: "/settings" },
  { path: "/market", component: () => import("@/views/Market.vue"), meta: { layout: "default", label_key: "menu.market" } },
  { path: "/logs", component: () => import("@/views/Logs.vue"), meta: { layout: "default", label_key: "menu.logs" } },
  { path: "/chat", component: () => import("@/views/Chat.vue"), meta: { layout: "default", label_key: "menu.chat" } },
  { path: "/extension/:key", component: () => import("@/views/ExtensionPage.vue"), meta: { layout: "default" } },
];
```

- [ ] **Step 2: Update `frontend/src/stores/menu.ts`**

Replace `config` and `plugins` entries with a single `settings` entry. The builtin items should look like:

```ts
const BUILTIN_ITEMS: MenuItem[] = [
  { path: "/", label_key: "menu.dashboard", icon: "mdi:view-dashboard" },
  { path: "/settings", label_key: "menu.settings", icon: "mdi:cog" },
  { path: "/market", label_key: "menu.market", icon: "mdi:store" },
  { path: "/logs", label_key: "menu.logs", icon: "mdi:file-document" },
  { path: "/chat", label_key: "menu.chat", icon: "mdi:chat" },
];
```

- [ ] **Step 3: Update `src/entari_plugin_webui/api/menus.py`**

Replace the two menu entries with one:

```python
BUILTIN_MENUS: list[dict] = [
    {"path": "/", "label_key": "menu.dashboard", "icon": "mdi:view-dashboard"},
    {"path": "/settings", "label_key": "menu.settings", "icon": "mdi:cog"},
    {"path": "/market", "label_key": "menu.market", "icon": "mdi:store"},
    {"path": "/logs", "label_key": "menu.logs", "icon": "mdi:file-document"},
    {"path": "/chat", "label_key": "menu.chat", "icon": "mdi:chat"},
]
```

- [ ] **Step 4: Update `frontend/src/i18n/zh-CN.ts`**

Add `menu.settings` and keep old keys for backward compatibility:

```ts
menu: { dashboard: "仪表盘", settings: "设置", market: "插件市场", logs: "实时日志", chat: "聊天室" },
```

Remove `plugins` and `config` from this object (they are no longer used by the menu).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/router/index.ts frontend/src/stores/menu.ts src/entari_plugin_webui/api/menus.py frontend/src/i18n/zh-CN.ts
git commit -m "feat(settings): add /settings route and unified menu"
```

---

### Task 2: Create the Settings Store

**Files:**
- Create: `frontend/src/stores/settings.ts`

- [ ] **Step 1: Write the store**

```ts
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import api from "@/api/client";

export const META_KEYS = ["$prefix", "$files", "$prelude", "$disable", "$priority", "$filter", "$optional"];

export interface PluginInfo {
  id: string;
  name: string;
  description?: string;
  version?: string;
  enabled: boolean;
  is_static: boolean;
  configurable: boolean;
}

function splitSchema(schema: any) {
  const properties = schema?.properties || {};
  const metaProps: Record<string, any> = {};
  const configProps: Record<string, any> = {};
  for (const [key, value] of Object.entries(properties)) {
    if (META_KEYS.includes(key)) metaProps[key] = value;
    else configProps[key] = value;
  }
  const metaSchema = Object.keys(metaProps).length
    ? { ...schema, properties: metaProps, required: (schema.required || []).filter((k: string) => META_KEYS.includes(k)) }
    : null;
  const configSchema = Object.keys(configProps).length
    ? { ...schema, properties: configProps, required: (schema.required || []).filter((k: string) => !META_KEYS.includes(k)) }
    : null;
  return { metaSchema, configSchema };
}

function splitData(data: any) {
  const metaData: Record<string, any> = {};
  const configData: Record<string, any> = {};
  if (data && typeof data === "object" && !Array.isArray(data)) {
    for (const [key, value] of Object.entries(data)) {
      if (META_KEYS.includes(key)) metaData[key] = value;
      else configData[key] = value;
    }
  }
  return { metaData, configData };
}

export const useSettingsStore = defineStore("settings", () => {
  const pluginList = ref<PluginInfo[]>([]);
  const currentSection = ref<string>("basic");
  const rawSchema = ref<any>(null);
  const metaSchema = ref<any>(null);
  const configSchema = ref<any>(null);
  const metaData = ref<Record<string, any>>({});
  const configData = ref<any>({});
  const loading = ref(false);
  const isDirty = ref(false);
  const savePending = ref(false);
  const error = ref<string>("");

  const isPluginSection = computed(() => currentSection.value.startsWith("plugins:"));
  const pluginId = computed(() => (isPluginSection.value ? currentSection.value.slice(8) : ""));
  const currentPlugin = computed(() => pluginList.value.find((p) => p.id === pluginId.value));

  async function loadPlugins() {
    try {
      const r = await api.get("/api/plugins");
      pluginList.value = (r.data.data || []).map((p: any) => ({
        id: p.id,
        name: p.name,
        description: p.description,
        version: p.version,
        enabled: p.enabled,
        is_static: p.is_static,
        configurable: p.configurable,
      }));
    } catch (e: any) {
      error.value = "加载插件列表失败";
    }
  }

  async function loadSection(section: string) {
    loading.value = true;
    error.value = "";
    currentSection.value = section;
    try {
      const [schemaR, dataR] = await Promise.all([
        api.get(`/api/config/${section}/schema`),
        api.get(`/api/config/${section}`),
      ]);
      rawSchema.value = schemaR.data.schema;
      const { metaSchema: ms, configSchema: cs } = splitSchema(rawSchema.value);
      metaSchema.value = ms;
      configSchema.value = cs;
      const rawData = dataR.data.data ?? {};
      const { metaData: md, configData: cd } = splitData(rawData);
      metaData.value = md;
      configData.value = cd;
      isDirty.value = false;
    } catch (e: any) {
      error.value = "加载配置失败";
      rawSchema.value = null;
      metaSchema.value = null;
      configSchema.value = null;
      metaData.value = {};
      configData.value = {};
    } finally {
      loading.value = false;
    }
  }

  function markDirty() {
    isDirty.value = true;
  }

  async function save() {
    savePending.value = true;
    error.value = "";
    const merged = { ...metaData.value, ...configData.value };
    try {
      if (isPluginSection.value) {
        await api.put(`/api/plugins/${pluginId.value}/config`, { config: merged });
      } else {
        await api.put(`/api/config/${currentSection.value}`, { data: merged });
      }
      isDirty.value = false;
      return true;
    } catch (e: any) {
      error.value = "保存失败";
      return false;
    } finally {
      savePending.value = false;
    }
  }

  async function togglePlugin(pluginId: string, enable: boolean) {
    await api.post(`/api/plugins/${pluginId}/toggle`, { enable });
    const p = pluginList.value.find((x) => x.id === pluginId);
    if (p) p.enabled = enable;
  }

  async function reloadPlugin(pluginId: string) {
    await api.post(`/api/plugins/${pluginId}/reload`);
  }

  return {
    pluginList,
    currentSection,
    metaSchema,
    configSchema,
    metaData,
    configData,
    loading,
    isDirty,
    savePending,
    error,
    isPluginSection,
    pluginId,
    currentPlugin,
    loadPlugins,
    loadSection,
    markDirty,
    save,
    togglePlugin,
    reloadPlugin,
  };
});
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/stores/settings.ts
git commit -m "feat(settings): add settings store with schema/data split"
```

---

### Task 3: Create SettingsSidebar Component

**Files:**
- Create: `frontend/src/components/settings/SettingsSidebar.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <div class="settings-sidebar">
    <el-input v-model="keyword" placeholder="搜索插件" clearable />
    <el-scrollbar class="menu-scroll">
      <div class="group">
        <div class="group-title">基础配置</div>
        <div
          :class="['menu-item', { active: store.currentSection === 'basic' }]"
          @click="select('basic')"
        >基础配置</div>
      </div>
      <div class="group">
        <div class="group-title">适配器</div>
        <div
          :class="['menu-item', { active: store.currentSection === 'adapters' }]"
          @click="select('adapters')"
        >适配器</div>
      </div>
      <div class="group">
        <div class="group-title">插件</div>
        <div
          :class="['menu-item', { active: store.currentSection === 'plugins' }]"
          @click="select('plugins')"
        >插件全局</div>
        <div
          v-for="p in filteredPlugins"
          :key="p.id"
          :class="['menu-item', { active: store.currentSection === `plugins:${p.id}` }]"
          @click="select(`plugins:${p.id}`)"
        >
          <span class="name">{{ p.name }}</span>
          <el-tag v-if="!p.enabled" type="info" size="small" class="status">已停用</el-tag>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useSettingsStore } from "@/stores/settings";

const store = useSettingsStore();
const keyword = ref("");

const filteredPlugins = computed(() => {
  if (!keyword.value) return store.pluginList;
  const q = keyword.value.toLowerCase();
  return store.pluginList.filter((p) => p.name.toLowerCase().includes(q));
});

async function select(section: string) {
  if (store.isDirty) {
    const ok = confirm("当前修改未保存，切换后将丢失，是否继续？");
    if (!ok) return;
  }
  await store.loadSection(section);
}
</script>

<style scoped>
.settings-sidebar {
  width: 260px;
  display: flex;
  flex-direction: column;
  padding: 16px;
  border-right: 1px solid var(--el-border-color);
}
.menu-scroll {
  flex: 1;
  margin-top: 12px;
}
.group {
  margin-bottom: 16px;
}
.group-title {
  font-weight: bold;
  color: var(--el-text-color-primary);
  padding: 8px 12px;
}
.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin: 2px 0;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}
.menu-item:hover {
  background: var(--el-fill-color-light);
}
.menu-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.status {
  margin-left: 8px;
  flex-shrink: 0;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/settings/SettingsSidebar.vue
git commit -m "feat(settings): add settings sidebar with search"
```

---

### Task 4: Create PluginHeader Component

**Files:**
- Create: `frontend/src/components/settings/PluginHeader.vue`

- [ ] **Step 1: Write the component**

```vue
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}
.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/settings/PluginHeader.vue
git commit -m "feat(settings): add plugin header component"
```

---

### Task 5: Create MetaSettings Component

**Files:**
- Create: `frontend/src/components/settings/MetaSettings.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <el-card class="meta-card" v-if="schema">
    <template #header>元数据设置</template>
    <SchemaForm v-if="schema" :schema="schema" v-model="model" />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SchemaForm from "@/components/schema-form/SchemaForm.vue";

const props = defineProps<{ schema: any; modelValue: any }>();
const emit = defineEmits<["update:modelValue"]>();

const model = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});
</script>

<style scoped>
.meta-card {
  margin-bottom: 16px;
  background: var(--el-fill-color-light);
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/settings/MetaSettings.vue
git commit -m "feat(settings): add meta settings card"
```

---

### Task 6: Create Settings View

**Files:**
- Create: `frontend/src/views/Settings.vue`

- [ ] **Step 1: Write the view**

```vue
<template>
  <div class="settings-page">
    <SettingsSidebar />
    <div class="settings-main">
      <el-skeleton v-if="store.loading" :rows="10" animated />
      <template v-else>
        <PluginHeader
          v-if="store.currentPlugin"
          :plugin="store.currentPlugin"
          @toggle="(v) => onToggle(v)"
          @reload="onReload"
          @detail="detailPlugin = store.currentPlugin"
        />
        <div v-else class="section-header">
          <h3>{{ sectionTitle }}</h3>
        </div>

        <el-alert v-if="store.error" :title="store.error" type="error" :closable="false" class="mb-4" />

        <MetaSettings
          v-if="store.metaSchema"
          :schema="store.metaSchema"
          v-model="store.metaData"
          @update:model-value="store.markDirty"
        />

        <el-card v-if="store.configSchema">
          <template #header>配置</template>
          <DualConfigEditor :key="store.currentSection" :schema="store.configSchema" v-model="store.configData" lang="json" @update:model-value="store.markDirty" />
        </el-card>

        <el-empty v-if="!store.metaSchema && !store.configSchema && !store.loading" description="无配置项" />

        <div class="actions">
          <el-button type="primary" :loading="store.savePending" @click="save">保存</el-button>
        </div>
      </template>
    </div>

    <el-dialog v-model="detailVisible" width="600" :title="detailPlugin?.name">
      <PluginDetailModal :plugin="detailPlugin" v-if="detailPlugin" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useSettingsStore, type PluginInfo } from "@/stores/settings";
import SettingsSidebar from "@/components/settings/SettingsSidebar.vue";
import PluginHeader from "@/components/settings/PluginHeader.vue";
import MetaSettings from "@/components/settings/MetaSettings.vue";
import DualConfigEditor from "@/components/config/DualConfigEditor.vue";
import PluginDetailModal from "@/components/plugins/PluginDetailModal.vue";

defineOptions({ name: "Settings" });

const route = useRoute();
const router = useRouter();
const store = useSettingsStore();
const detailPlugin = ref<PluginInfo | null>(null);
const detailVisible = computed({ get: () => !!detailPlugin.value, set: (v) => { if (!v) detailPlugin.value = null; } });

const sectionTitle = computed(() => {
  const map: Record<string, string> = { basic: "基础配置", adapters: "适配器", plugins: "插件全局" };
  return map[store.currentSection] || store.currentSection;
});

async function save() {
  const ok = await store.save();
  if (ok) ElMessage.success("设置已保存");
  else ElMessage.error("保存失败");
}

async function onToggle(v: boolean) {
  if (!store.currentPlugin) return;
  await store.togglePlugin(store.currentPlugin.id, v);
  ElMessage.success(v ? "已启用" : "已停用");
}

async function onReload() {
  if (!store.currentPlugin) return;
  await store.reloadPlugin(store.currentPlugin.id);
  ElMessage.success("已重载");
}

onMounted(async () => {
  await store.loadPlugins();
  const section = route.query.section as string || "basic";
  await store.loadSection(section);
});

watch(() => route.query.section, async (section) => {
  if (typeof section === "string" && section !== store.currentSection) {
    await store.loadSection(section);
  }
});
</script>

<style scoped>
.settings-page {
  display: flex;
  height: 100%;
}
.settings-main {
  flex: 1;
  min-width: 0;
  padding: 16px;
  overflow-y: auto;
}
.section-header {
  margin-bottom: 16px;
}
.section-header h3 {
  margin: 0;
}
.actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.mb-4 {
  margin-bottom: 16px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Settings.vue
git commit -m "feat(settings): add settings view"
```

---

### Task 7: Update Dashboard Links

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

- [ ] **Step 1: Update buttons**

Find these lines:

```vue
<el-button @click="$router.push('/plugins')">插件管理</el-button>
<el-button @click="$router.push('/config')">配置管理</el-button>
```

Replace with:

```vue
<el-button @click="$router.push('/settings')">设置</el-button>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "fix(dashboard): update link to /settings"
```

---

### Task 8: Remove Old Views

**Files:**
- Delete: `frontend/src/views/Config.vue`
- Delete: `frontend/src/views/Plugins.vue`

- [ ] **Step 1: Delete files**

```bash
rm frontend/src/views/Config.vue frontend/src/views/Plugins.vue
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "refactor(settings): remove old Config and Plugins views"
```

---

### Task 9: Update Tests

**Files:**
- Modify: `tests/api/test_plugins.py` (if it asserts menu entries)

- [ ] **Step 1: Run existing tests**

```bash
pdm run pytest -q
```

If `test_menus` fails because it expects old menu keys, update the expected list to:

```python
expected = ["menu.dashboard", "menu.settings", "menu.market", "menu.logs", "menu.chat"]
```

- [ ] **Step 2: Commit**

```bash
git add tests/api/test_plugins.py
git commit -m "test: update menu expectations for unified settings"
```

---

### Task 10: Build and Final Verification

- [ ] **Step 1: Run frontend build**

```bash
cd frontend && npm run build
```

Expected: `vue-tsc --noEmit && vite build` completes with no errors.

- [ ] **Step 2: Run backend tests**

```bash
pdm run pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Commit any final fixes**

```bash
git add -A
git commit -m "fix(settings): final build/test adjustments"
```

---

## Spec Coverage Check

| Spec Requirement | Implementing Task |
|------------------|-------------------|
| `/settings` route + redirects | Task 1 |
| `?section=` query param | Task 6 |
| Left sidebar with 3 expanded groups | Task 3 |
| Plugin search filter | Task 3 |
| Plugin header with actions | Task 4 |
| Meta settings for `$prefix/$files/$prelude` | Tasks 2, 5 |
| Meta settings for `$disable/$filter/$priority/$optional` | Tasks 2, 5 |
| Regular config in `DualConfigEditor` | Task 6 |
| Dirty state prompt | Task 3 |
| Unified save feedback | Task 6 |
| Dashboard link update | Task 7 |
| Menu merge | Task 1 |

## Placeholder Scan

No placeholders. All code blocks contain runnable code. All commands have expected outputs.
