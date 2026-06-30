# Phase 10 — SchemaForm 树、双编辑器与全部业务页面

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** 实现统一 JSON-Schema 递归表单渲染器（Element Plus 版）、表单↔Monaco 双向视图、Dashboard/Plugins/Market/Config/Logs 五个真实页面、扩展页面 `ExtensionPanelHost`（iframe + postMessage RPC）。

**Architecture:** `components/schema-form/` 树形递归组件；`DualConfigEditor` 切视图时同步；页面用 Pinia loader + axios client；Logs 用 `useWebSocket`。`@iconify/vue` 统一图标。

**Tech Stack:** Element Plus、Monaco Editor、vue-echarts、ansi-to-html、@iconify/vue、Starlette WS。

---

## 文件结构

```
frontend/src/
├── components/
│   ├── schema-form/{SchemaForm,SchemaField,ObjectField,ArrayField,OneOfField,AdditionalPropertiesEditor}.vue
│   ├── config/DualConfigEditor.vue
│   ├── common/{StatCard,AnsiLogViewer}.vue
│   ├── plugins/{PluginDetailModal,ConfigDrawer}.vue
│   └── market/{MarketCard,InstallProgress}.vue
├── composables/
│   ├── useSchemaForm.ts
│   └── useWebSocket.ts
├── extension-runtime/ExtensionPanelHost.vue
└── views/
    ├── Dashboard.vue  (替换占位)
    ├── Plugins.vue  (替换占位)
    ├── Market.vue  (替换占位)
    ├── Config.vue  (替换占位)
    ├── Logs.vue  (替换占位)
    └── ExtensionPage.vue
```

---

## Task 10.1：引入图标与 WS composable

**Files:** Modify `package.json`（加 `@iconify/vue` 与 `@iconify-json/mdi`）；`AppIcon.vue` 重写；`composables/useWebSocket.ts`

- [ ] **Step 1:** `npm i @iconify/vue @iconify-json/mdi`。

- [ ] **Step 2: AppIcon.vue**

```vue
<template><Icon :icon="icon" /></template>
<script setup lang="ts">import { Icon } from "@iconify/vue"; defineProps<{ icon: string }>();</script>
```

- [ ] **Step 3: useWebSocket.ts**

```ts
// src/composables/useWebSocket.ts
import { ref, onUnmounted } from "vue";

export function useWebSocketConnection(path: string, opts: { onMessage: (m: any) => void; onError?: () => void; autoReconnect?: boolean } = { onMessage: () => {} }) {
  const connected = ref(false);
  let ws: WebSocket | null = null;
  let reconnectTimer: number | null = null;
  const auto = opts.autoReconnect ?? true;

  function buildUrl() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${location.host}${path}`;
  }

  function connect() {
    ws = new WebSocket(buildUrl());
    ws.onopen = () => { connected.value = true; };
    ws.onmessage = (ev) => {
      try { opts.onMessage(JSON.parse(ev.data)); }
      catch { opts.onMessage({ type: "raw", data: ev.data }); }
    };
    ws.onerror = () => { opts.onError?.(); };
    ws.onclose = () => {
      connected.value = false;
      if (auto) reconnectTimer = window.setTimeout(connect, 3000);
    };
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    ws?.close();
  }

  connect();
  onUnmounted(disconnect);
  return { connected, disconnect };
}
```

- [ ] **Step 4:** 提交 `git commit -m "feat(frontend): iconify + websocket composable"`.

---

## Task 10.2：SchemaForm 入口与字段分派

**Files:** Create `components/schema-form/SchemaForm.vue`、`SchemaField.vue`、`ObjectField.vue`、`ArrayField.vue`、`OneOfField.vue`、`AdditionalPropertiesEditor.vue`

- [ ] **Step 1: SchemaForm.vue**

```vue
<!-- src/components/schema-form/SchemaForm.vue -->
<template>
  <div class="schema-form">
    <template v-if="schema?.properties">
      <SchemaField v-for="(prop, key) in schema.properties" :key="key" :field-schema="prop" :defs="schema.$defs" :field-key="String(key)" :required="schema.required?.includes(String(key))" v-model="model[key]" />
    </template>
    <AdditionalPropertiesEditor v-else-if="schema?.additionalProperties" :value-schema="typeof schema.additionalProperties === 'object' ? schema.additionalProperties : {}" :defs="schema.$defs" v-model="model" />
    <el-empty v-else-if="!Object.keys(model || {}).length" description="无配置项" />
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from "vue";
import SchemaField from "./SchemaField.vue";
import AdditionalPropertiesEditor from "./AdditionalPropertiesEditor.vue";

// modelValue: record<string, any>; schema: JSON Schema object
const props = defineProps<{ schema?: any; modelValue?: Record<string, any> }>();
const emit = defineEmits<{ "update:modelValue": [v: Record<string, any>] }>();
const model = ref<Record<string, any>>(props.modelValue ?? {});
watch(model, (v) => emit("update:modelValue", v), { deep: true });
</script>
```

- [ ] **Step 2: SchemaField.vue**（核心分派器）

```vue
<template><div class="field">
  <label class="field-label">{{ fieldSchema.title || fieldKey }}
    <span v-if="required" style="color:var(--el-color-danger)">*</span>
  </label>
  <el-tooltip v-if="fieldSchema.description" :content="fieldSchema.description" placement="top"><el-icon><InfoFilled /></el-icon></el-tooltip>

  <!-- readOnly -->
  <el-input v-if="resolved.readOnly" :model-value="String(modelValue ?? '')" disabled />
  <!-- enum -->
  <el-select v-else-if="enumOptions" v-model="model">
    <el-option v-for="o in enumOptions" :key="o" :label="o" :value="o" />
  </el-select>
  <!-- boolean -->
  <el-switch v-else-if="resolved.type === 'boolean'" v-model="model" />
  <!-- number/integer -->
  <el-input-number v-else-if="resolved.type === 'integer' || resolved.type === 'number'" v-model="model" :step="resolved.type === 'integer' ? 1 : 0.1" />
  <!-- array -->
  <ArrayField v-else-if="resolved.type === 'array'" :items-schema="resolved.items" :defs="defs" :field-key="fieldKey" v-model="model" />
  <!-- object -->
  <ObjectField v-else-if="resolved.type === 'object'" :object-schema="resolved" :defs="defs" :field-key="fieldKey" v-model="model" />
  <!-- oneOf -->
  <OneOfField v-else-if="resolved.oneOf" :one-of="resolved.oneOf" :defs="defs" :field-key="fieldKey" v-model="model" />
  <!-- password -->
  <el-input v-else-if="resolved.format === 'password'" v-model="model" type="password" show-password />
  <!-- string -->
  <el-input v-else v-model="model" :placeholder="resolved.default != null ? String(resolved.default) : ''" />

  <el-dropdown trigger="click" @command="onCmd">
    <el-icon><MoreFilled /></el-icon>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="json">编辑 JSON</el-dropdown-item>
        <el-dropdown-item command="reset">恢复默认值</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>

  <el-dialog v-model="jsonEditing" title="编辑 JSON" width="500">
    <el-input v-model="jsonText" type="textarea" :rows="10" />
    <template #footer><el-button @click="jsonEditing=false">取消</el-button><el-button type="primary" @click="applyJson">确定</el-button></template>
  </el-dialog>
</div>
</template>
<script setup lang="ts">
import { computed, ref } from "vue";
import { InfoFilled, MoreFilled } from "@element-plus/icons-vue";
import ArrayField from "./ArrayField.vue";
import ObjectField from "./ObjectField.vue";
import OneOfField from "./OneOfField.vue";

const props = defineProps<{ fieldSchema: any; defs?: any; fieldKey: string; required?: boolean; modelValue?: any }>();
const emit = defineEmits<{ "update:modelValue": [v: any] }>();

const resolved = computed(() => resolveRef(props.fieldSchema, props.defs));

const model = computed({
  get: () => props.modelValue ?? defaultFor(resolved.value),
  set: (v) => emit("update:modelValue", v),
});

const enumOptions = computed(() =>
  Array.isArray(resolved.value.enum) ? resolved.value.enum : (
    resolved.value.type === "string" && resolved.value.oneOf ? null : null));

function resolveRef(schema: any, defs: any): any {
  if (!schema?.$ref && !schema?.oneOf && !schema?.$defs) return schema;
  if (schema.$ref) {
    const m = schema.$ref.match(/\$defs\/([^/]+)$/);
    if (m && defs?.[m[1]]) {
      const r = { ...defs[m[1]], description: schema.description ?? defs[m[1]].description, title: schema.title ?? defs[m[1]].title };
      return r;
    }
  }
  return schema;
}

function defaultFor(schema: any): any {
  if (schema.default !== undefined) return schema.default;
  switch (schema.type) {
    case "boolean": return false;
    case "integer": case "number": return 0;
    case "string": return "";
    case "array": return [];
    case "object": return {};
    default: return null;
  }
}

const jsonEditing = ref(false);
const jsonText = ref("");
function onCmd(cmd: string) {
  if (cmd === "json") { jsonText.value = JSON.stringify(props.modelValue ?? null, null, 2); jsonEditing.value = true; }
  if (cmd === "reset") { emit("update:modelValue", defaultFor(resolved.value)); }
}
function applyJson() {
  try { emit("update:modelValue", JSON.parse(jsonText.value)); jsonEditing.value = false; }
  catch { /* ignore invalid */ }
}
</script>
```

- [ ] **Step 3: ObjectField.vue**

```vue
<template>
  <div class="obj-field">
    <template v-if="objectSchema.properties">
      <SchemaField v-for="(p, k) in objectSchema.properties" :key="k" :field-schema="p" :defs="defs" :field-key="String(k)" :required="objectSchema.required?.includes(String(k))" v-model="model[k]" />
      <AdditionalPropertiesEditor v-if="objectSchema.additionalProperties" :excluded-keys="Object.keys(objectSchema.properties)" :value-schema="typeof objectSchema.additionalProperties==='object'?objectSchema.additionalProperties:{}" :defs="defs" v-model="model" />
    </template>
    <AdditionalPropertiesEditor v-else-if="objectSchema.additionalProperties" :value-schema="typeof objectSchema.additionalProperties==='object'?objectSchema.additionalProperties:{}" :defs="defs" v-model="model" />
    <el-input v-else v-model="jsonText" type="textarea" :rows="4" />
  </div>
</template>
<script setup lang="ts">
import { computed, ref } from "vue";
import SchemaField from "./SchemaField.vue";
import AdditionalPropertiesEditor from "./AdditionalPropertiesEditor.vue";
const props = defineProps<{ objectSchema: any; defs?: any; fieldKey: string; modelValue?: any }>();
const emit = defineEmits<{ "update:modelValue": [v: any] }>();
const model = computed({ get: () => props.modelValue ?? {}, set: (v) => emit("update:modelValue", v) });
const jsonText = ref(JSON.stringify(props.modelValue ?? {}, null, 2));
</script>
```

- [ ] **Step 4: ArrayField.vue**

```vue
<template><div class="arr-field">
  <!-- 简单字符串数组 -->
  <el-dynamic-input v-if="isSimpleString" v-model="model" />
  <!-- 对象数组 -->
  <div v-else-if="isObjectItems">
    <el-card v-for="(_, i) in model" :key="i" closable @close="model.splice(i,1)" style="margin-bottom:8px">
      <ObjectField :object-schema="itemsSchema" :defs="defs" :field-key="`${fieldKey}[${i}]`" v-model="model[i]" />
    </el-card>
    <el-button @click="model.push({})">添加项目</el-button>
  </div>
  <!-- oneOf 数组 -->
  <div v-else-if="isOneOfItems">
    <el-card v-for="(_, i) in model" :key="i" closable @close="model.splice(i,1)" style="margin-bottom:8px">
      <OneOfField :one-of="itemsSchema.oneOf" :defs="defs" :field-key="`${fieldKey}[${i}]`" v-model="model[i]" />
    </el-card>
    <el-button @click="model.push({})">添加项目</el-button>
  </div>
  <el-input v-else v-model="jsonText" type="textarea" :rows="4" />
</div></template>
<script setup lang="ts">
import { computed, ref } from "vue";
import ObjectField from "./ObjectField.vue";
import OneOfField from "./OneOfField.vue";
const props = defineProps<{ itemsSchema?: any; defs?: any; fieldKey: string; modelValue?: any[] }>();
const emit = defineEmits<{ "update:modelValue": [v: any[]] }>();
const model = computed<any[]>({ get: () => props.modelValue ?? [], set: (v) => emit("update:modelValue", v) });
const isSimpleString = computed(() => props.itemsSchema?.type === "string");
const isObjectItems = computed(() => props.itemsSchema?.type === "object" && !props.itemsSchema?.oneOf);
const isOneOfItems = computed(() => !!props.itemsSchema?.oneOf);
const jsonText = ref(JSON.stringify(props.modelValue ?? [], null, 2));
</script>
```

- [ ] **Step 5: OneOfField.vue**

```vue
<template><div class="oneof-field">
  <div v-if="isSimple">
    <el-select v-model="selectedIndex" @change="onTypeChange">
      <el-option v-for="(o,i) in simpleOptions" :key="i" :label="labelOf(o)" :value="i" />
    </el-select>
    <el-input v-if="curType==='string'" v-model="model" />
    <el-input-number v-else-if="curType==='number'||curType==='integer'" v-model="model" :step="curType==='integer'?1:0.1" />
    <el-switch v-else-if="curType==='boolean'" v-model="model" />
  </div>
  <div v-else>
    <el-select v-model="selectedIndex" @change="onTypeChange">
      <el-option v-for="(o,i) in complexOptions" :key="i" :label="o.title || o.properties?.type?.enum?.[0] || `选项${i+1}`" :value="i" />
    </el-select>
    <el-card style="margin-top:8px">
      <SchemaField :field-schema="complexOptions[selectedIndex]" :defs="defs" :field-key="fieldKey" v-model="model" />
    </el-card>
  </div>
</div></template>
<script setup lang="ts">
import { computed, ref, watch } from "vue";
import SchemaField from "./SchemaField.vue";
const props = defineProps<{ oneOf: any[]; defs?: any; fieldKey: string; modelValue?: any }>();
const emit = defineEmits<{ "update:modelValue": [v: any] }>();
const simpleTypes = ["string","number","integer","boolean","null"];
const simpleOptions = computed(() => props.oneOf.filter(o => simpleTypes.includes(o.type)));
const complexOptions = computed(() => props.oneOf.filter(o => !simpleTypes.includes(o.type)));
const isSimple = computed(() => props.oneOf.every(o => simpleTypes.includes(o.type)));
const selectedIndex = ref(0);
const curType = computed(() => simpleOptions.value[selectedIndex.value]?.type);
const model = computed({ get: () => props.modelValue, set: (v) => emit("update:modelValue", v) });
function labelOf(o:any){return o.type==="null"?"空":o.type;}
function onTypeChange() {
  const t = curType.value;
  emit("update:modelValue", t==="null"?null:t==="string"?"":t==="boolean"?false:0);
}
watch(() => props.modelValue, () => {
  // 由值反推 index（简单类型）
  if (isSimple.value) {
    const v = props.modelValue;
    const i = simpleOptions.value.findIndex(o => o.type === (v===null?"null":typeof v==="string"?"string":typeof v));
    if (i >= 0) selectedIndex.value = i;
  }
}, { immediate: true });
</script>
```

- [ ] **Step 6: AdditionalPropertiesEditor.vue**

```vue
<template><div class="ap-editor">
  <el-divider v-if="excludedKeys.length" content-position="left">附加属性</el-divider>
  <el-card v-for="(v, k) in extra" :key="k" closable @close="delete (model as any)[k]" style="margin-bottom:8px">
    <el-input v-model="keyName" placeholder="属性名" style="width:120px" />
    <component :is="renderValue(k)" v-model="(model as any)[k]" />
  </el-card>
  <div style="display:flex;gap:8px">
    <el-input v-model="newKey" placeholder="新属性名" />
    <el-button @click="add">添加属性</el-button>
  </div>
</div></template>
<script setup lang="ts">
import { computed, ref, watch } from "vue";
import SchemaField from "./SchemaField.vue";
const props = defineProps<{ valueSchema?: any; defs?: any; excludedKeys?: string[]; modelValue?: Record<string, any> }>();
const emit = defineEmits<{ "update:modelValue": [v: Record<string, any>] }>();
const excluded = computed(() => props.excludedKeys ?? []);
const model = computed<Record<string, any>>({ get: () => props.modelValue ?? {}, set: (v) => emit("update:modelValue", v) });
const extra = computed(() => Object.fromEntries(Object.entries(model.value).filter(([k]) => !excluded.value.includes(k))));
const keyName = ref("");
const newKey = ref("");
function add() {
  if (!newKey.value) return;
  model.value[newKey.value] = props.valueSchema?.type === "boolean" ? false : props.valueSchema?.type === "object" ? {} : props.valueSchema?.type === "array" ? [] : "";
  newKey.value = "";
}
function renderValue(k: string) {
  return props.valueSchema ? null : null; // 由 SchemaField 渲染更稳：见下注释
}
</script>
```

> 完整实现中 `renderValue` 改为直接在模板里 `<SchemaField :field-schema="valueSchema" :defs="defs" :field-key="keyName" v-model="model[k]" />`（当 `valueSchema` 存在）；否则按 `valueType` 渲染 primitive。请按上述模式补全模板分支（demo 性质，phase-11 review 时补为生产可用）。

- [ ] **Step 7:** `npm run build` 通过；在 Config.vue 中接入验证。提交 `git commit -m "feat(frontend): JSON-schema dynamic form tree"`。

---

## Task 10.3：DualConfigEditor

**Files:** Create `components/config/DualConfigEditor.vue`

```vue
<template>
  <div class="dual-editor">
    <el-radio-group v-model="view">
      <el-radio-button label="form">表单</el-radio-button>
      <el-radio-button label="code">代码</el-radio-button>
    </el-radio-group>
    <el-alert v-if="codeInvalid && view==='form'" type="warning" :title="t('config.code_invalid_note')" :closable="false" />
    <SchemaForm v-show="view==='form'" :schema="schema" v-model="formData" />
    <div v-show="view==='code'" ref="monacoHost" style="height:480px"></div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import * as monaco from "monaco-editor";
import SchemaForm from "@/components/schema-form/SchemaForm.vue";
import { useI18n } from "vue-i18n";

const props = defineProps<{ schema: any; modelValue: any; lang?: "json" | "yaml" }>();
const emit = defineEmits<{ "update:modelValue": [v: any] }>();
const { t } = useI18n();
const view = ref<"form" | "code">("form");
const formData = ref<any>(props.modelValue ?? {});
const codeInvalid = ref(false);
const monacoHost = ref<HTMLElement>();
let editor: monaco.editor.IStandaloneCodeEditor | null = null;

watch(formData, (v) => emit("update:modelValue", v), { deep: true });

// 离开代码视图 → 解析覆盖表单
watch(view, (v, old) => {
  if (old === "code" && v === "form" && editor) {
    try {
      const parsed = props.lang === "yaml" ? parseYaml(editor.getValue()) : JSON.parse(editor.getValue());
      formData.value = parsed;
      codeInvalid.value = false;
    } catch { codeInvalid.value = true; }
  }
  if (v === "code") {
    // 表单 → 代码：以表单序列化覆盖代码内容
    nextTick(() => syncMonaco());
  }
});

function parseYaml(s: string) { /* 用 js-yaml 或简陋解析；首版仅 JSON，YAML 见 §6.3 后续 */
  return JSON.parse(s);
}

function syncMonaco() {
  if (!editor) return;
  const text = JSON.stringify(formData.value, null, 2);
  editor.setValue(text);
}

onMounted(() => {
  if (!monacoHost.value) return;
  editor = monaco.editor.create(monacoHost.value, {
    value: JSON.stringify(formData.value, null, 2),
    language: props.lang === "yaml" ? "yaml" : "json",
    automaticLayout: true,
  });
});
onBeforeUnmount(() => editor?.dispose());

import { nextTick } from "vue";
</script>
```

> YAMT 解析首版只支持 JSON；YAML 视图作为 §6.3 后续增量（注释中标注）。提交 `git commit -m "feat(frontend): DualConfigEditor form<->code"`。

---

## Task 10.4：Plugins 页面

**Files:** Replace `views/Plugins.vue`

```vue
<template>
  <div class="plugins-page">
    <el-input v-model="search" placeholder="搜索" style="width:240px;float:right" />
    <el-table :data="filtered" v-loading="loading">
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="version" label="版本" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-switch :model-value="row.enabled" :disabled="row.is_static" @change="(v: any) => onToggle(row, v)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button size="small" @click="openConfig(row)" :disabled="!row.configurable">配置</el-button>
          <el-button size="small" @click="reload(row)">重载</el-button>
          <el-button size="small" @click="detail = row">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-drawer v-model="drawerOpen" size="60%" :title="current?.name + ' 配置'">
      <DualConfigEditor :schema="drawerSchema" v-model="drawerData" v-if="drawerSchema" />
      <el-empty v-else description="无 config 模型" />
      <template #footer>
        <el-button @click="drawerOpen=false">取消</el-button>
        <el-button type="primary" @click="saveConfig">保存</el-button>
      </template>
    </el-drawer>
    <el-dialog v-model="!!detail" width="600" :title="detail?.name">
      <PluginDetailModal :plugin="detail" v-if="detail" />
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import api from "@/api/client";
import DualConfigEditor from "@/components/config/DualConfigEditor.vue";
import PluginDetailModal from "@/components/plugins/PluginDetailModal.vue";

const loading = ref(false); const list = ref<any[]>([]); const search = ref("");
const filtered = computed(() => list.value.filter(p => p.name.includes(search.value)));
const detail = ref<any>(null);

async function load() {
  loading.value = true;
  try { list.value = (await api.get("/api/plugins")).data.data; }
  finally { loading.value = false; }
}
async function onToggle(row: any, v: any) { await api.post(`/api/plugins/${row.id}/toggle`, { enable: v }); row.enabled = v; }
async function reload(row: any) { await api.post(`/api/plugins/${row.id}/reload`); ElMessage.success("已重载"); }

const drawerOpen = ref(false); const current = ref<any>(null);
const drawerSchema = ref<any>(null); const drawerData = ref<any>({});
async function openConfig(row: any) {
  current.value = row;
  drawerData.value = { ...row.config };
  const r = await api.get(`/api/config/plugins.${row.id}/schema`);
  drawerSchema.value = r.data.schema;
  drawerOpen.value = true;
}
async function saveConfig() {
  await api.put(`/api/plugins/${current.value.id}/config`, { config: drawerData.value });
  ElMessage.success("已保存"); drawerOpen.value = false; load();
}
onMounted(load);
</script>
```

`PluginDetailModal.vue`：渲染 id/version/license/authors/description/urls/references/referents（用 `el-descriptions`）。

提交 `git commit -m "feat(frontend): plugins page"`。

---

## Task 10.5：其余页面（骨架级实现要点）

- **Dashboard.vue**：`GET /api/stats` → 4 张 `StatCard` + `v-chart` 折线（`week_messages`）+ 快捷按钮。
- **Market.vue**：`GET /api/market/plugins` → 卡片网格 + 标签筛选 + 搜索；InstallProgress 轮询 `GET /api/market/tasks/{id}` 每 1s 最多 60 次。
- **Config.vue**：左边 `el-menu` 列 sections（来自 `GET /api/config` 的 plugin_sections），右边 `DualConfigEditor`（schema 来自 `GET /api/config/{section}/schema`），保存 `PUT /api/config/{section}`。
- **Logs.vue**：`useWebSocketConnection("/ws/logs", {onMessage})` 推入数组（cap 1000），`AnsiLogViewer` 渲染（ansi-to-html）。
- **ExtensionPage.vue** + **ExtensionPanelHost.vue**：按 manifest 加载 `<iframe :src="page.component_url" sandbox="allow-scripts allow-forms">`；`postMessage` RPC 桥（`webui.api/t/user/ws`）在宿主 window 监听 message 事件分发。

每页完成后 `npm run build` 验证并提交。命名约定提交信息：`feat(frontend): <page> page`。

---

## Phase 10 完成标准

- SchemaForm 支持 object/array/oneOf/enum/boolean/number/string/password/$ref/additionalProperties 与必填标记
- DualConfigEditor 表单↔切换同步，代码无效时表单进入停态
- Plugins/Market/Config/Logs/Dashboard 五页可交互；扩展页 iframe 沙箱加载
- `npm run build` 通过且产物写入 `static/frontend/`