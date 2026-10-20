<template>
  <div
    v-loading="pending"
    class="plugin-detail-panel"
  >
    <el-empty
      v-if="!plugin"
      description="选择左侧插件查看详情"
    />
    <template v-else>
      <header class="detail-header">
        <div class="title-row">
          <h2>{{ plugin.builtin_title || plugin.name }}</h2>
          <el-tag
            size="small"
            :type="statusType"
          >
            {{ statusLabel }}
          </el-tag>
          <el-tag
            v-if="plugin.version || detailVersion"
            size="small"
            effect="plain"
          >
            v{{ detailVersion || plugin.version }}
          </el-tag>
          <el-tag
            size="small"
            type="info"
            effect="plain"
          >
            {{ typeLabel }}
          </el-tag>
          <el-tag
            v-if="plugin.builtin_name && plugin.state === 'unavailable'"
            size="small"
            type="warning"
            effect="plain"
          >
            未配置
          </el-tag>
        </div>
        <div
          v-if="parentId"
          class="breadcrumb"
        >
          <span class="parent-label">父插件</span>
          <span>{{ parentId }}</span>
        </div>
        <p class="description">
          {{ description }}
        </p>
      </header>

      <div class="actions">
        <el-tooltip
          v-if="showSwitch"
          :content="toggleHint"
          :disabled="!toggleDisabled"
        >
          <span class="switch-row">
            <el-switch
              :model-value="plugin.state === 'enabled'"
              :disabled="toggleDisabled"
              @change="onSwitchChange"
            />
            <span class="switch-label">{{ plugin.state === "enabled" ? "已启用" : "已禁用" }}</span>
          </span>
        </el-tooltip>

        <el-button
          v-if="plugin.unloaded"
          type="primary"
          @click="emit('load')"
        >
          加载
        </el-button>
        <el-tooltip
          v-if="plugin.unloaded"
          content="加载后可编辑"
        >
          <span>
            <el-button disabled>
              编辑配置
            </el-button>
          </span>
        </el-tooltip>
        <el-button
          v-else-if="plugin.configurable"
          type="primary"
          @click="emit('config')"
        >
          编辑配置
        </el-button>

        <el-button
          v-if="canReload"
          @click="emit('reload')"
        >
          重载
        </el-button>
        <el-button
          v-if="canUnload"
          type="danger"
          plain
          @click="emit('unload')"
        >
          卸载
        </el-button>
        <el-button
          v-if="canDeletePackage"
          type="danger"
          @click="emit('uninstall')"
        >
          卸载并删除包
        </el-button>
        <el-button @click="emit('detail')">
          详情
        </el-button>
      </div>

      <el-alert
        v-if="plugin.disable_expr"
        class="expr-alert"
        type="warning"
        :closable="false"
        :title="`条件禁用表达式：${plugin.disable_expr}`"
      />

      <el-descriptions
        :column="2"
        border
        size="small"
        class="detail-descriptions"
      >
        <el-descriptions-item label="ID">
          {{ detailId }}
        </el-descriptions-item>
        <el-descriptions-item label="配置键">
          {{ configKey || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="类型">
          {{ typeLabel }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          {{ statusLabel }}
        </el-descriptions-item>
        <el-descriptions-item
          v-if="parentId"
          label="父插件"
        >
          {{ parentId }}
        </el-descriptions-item>
        <el-descriptions-item label="子插件数">
          {{ childCount }}
        </el-descriptions-item>
        <el-descriptions-item label="作者">
          {{ authors }}
        </el-descriptions-item>
        <el-descriptions-item label="License">
          {{ license || "-" }}
        </el-descriptions-item>
        <el-descriptions-item
          v-if="marketEntry"
          label="市场包"
        >
          {{ marketEntry.pip_name }}
        </el-descriptions-item>
        <el-descriptions-item
          v-if="urlEntries.length"
          label="URL"
          :span="2"
        >
          <div
            v-for="[key, url] in urlEntries"
            :key="key"
            class="url-row"
          >
            <el-link
              :href="url"
              target="_blank"
              type="primary"
            >
              {{ key }}
            </el-link>
          </div>
        </el-descriptions-item>
        <el-descriptions-item
          v-if="references.length"
          label="引用"
          :span="2"
        >
          <el-tag
            v-for="r in references"
            :key="r"
            size="small"
            class="ref-tag"
          >
            {{ r }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item
          v-if="referents.length"
          label="被引用"
          :span="2"
        >
          <el-tag
            v-for="r in referents"
            :key="r"
            size="small"
            type="info"
            class="ref-tag"
          >
            {{ r }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ManagedPlugin } from "@/stores/plugins";

const props = defineProps<{
  plugin: ManagedPlugin | null;
  detail?: Record<string, unknown> | null;
  pending?: boolean;
}>();

const emit = defineEmits<{
  toggle: [enable: boolean];
  reload: [];
  unload: [];
  uninstall: [];
  load: [];
  config: [];
  detail: [];
}>();

const detail = computed(() => props.detail ?? {});
const detailId = computed(() => String(detail.value.id ?? props.plugin?.id ?? props.plugin?.uid ?? "-"));
const detailVersion = computed(() => {
  const value = detail.value.version;
  return value ? String(value) : "";
});
const description = computed(() => {
  const value = detail.value.description;
  if (value) return String(value);
  if (props.plugin?.builtin_description) return props.plugin.builtin_description;
  if (props.plugin?.description) return props.plugin.description;
  return props.plugin?.has_metadata ? "无描述" : "无元数据";
});
const configKey = computed(() => {
  const value = detail.value.config_key ?? props.plugin?.key;
  return value ? String(value) : "";
});
const parentId = computed(() => {
  const value = detail.value.parent ?? props.plugin?.parent;
  return value ? String(value) : "";
});
const authors = computed(() => {
  const value = detail.value.authors;
  if (!value) return "-";
  return Array.isArray(value) ? value.join(", ") : String(value);
});
const license = computed(() => {
  const value = detail.value.license;
  return value ? String(value) : "";
});
const childCount = computed(() => {
  const value = detail.value.subplugins;
  return Array.isArray(value) ? value.length : 0;
});
const references = computed(() => {
  const value = detail.value.references;
  return Array.isArray(value) ? value.map(String) : [];
});
const referents = computed(() => {
  const value = detail.value.referents;
  return Array.isArray(value) ? value.map(String) : [];
});
const urlEntries = computed<[string, string][]>(() => {
  const value = detail.value.urls;
  if (!value) return [];
  if (Array.isArray(value)) return value.map((url, index) => [String(index), String(url)]);
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .filter(([, url]) => Boolean(url))
      .map(([key, url]) => [key, String(url)]);
  }
  return [];
});
const marketEntry = computed<{ name: string; pip_name: string } | null>(() => {
  const fromDetail = detail.value.market;
  if (fromDetail && typeof fromDetail === "object") {
    return fromDetail as { name: string; pip_name: string };
  }
  return props.plugin?.market ?? null;
});

const typeLabel = computed(() => {
  switch (props.plugin?.type) {
    case "rootless":
      return "根基";
    case "built-in":
      return "内建";
    case "local":
      return "本地";
    default:
      return "常规";
  }
});

const statusLabel = computed(() => {
  switch (props.plugin?.state) {
    case "enabled":
      return "已启用";
    case "disabled":
      return "已禁用";
    case "unloaded":
      return "已卸载";
    default:
      return "不可用";
  }
});

const statusType = computed<"success" | "warning" | "info">(() => {
  switch (props.plugin?.state) {
    case "enabled":
      return "success";
    case "disabled":
      return "warning";
    default:
      return "info";
  }
});

const showSwitch = computed(
  () => Boolean(props.plugin && !props.plugin.unloaded && props.plugin.type !== "rootless" && !props.plugin.is_static),
);
const toggleDisabled = computed(
  () => Boolean(props.pending || props.plugin?.parent_enabled === false),
);
const toggleHint = computed(() =>
  props.plugin?.parent_enabled === false ? "父插件未启用，不能单独操作子插件" : "",
);
const canReload = computed(
  () => Boolean(props.plugin && !props.plugin.unloaded && props.plugin.type !== "rootless" && !props.plugin.is_static),
);
const canUnload = computed(
  () =>
    Boolean(
      props.plugin &&
        !props.plugin.unloaded &&
        props.plugin.can_unload &&
        props.plugin.type !== "rootless" &&
        !props.plugin.is_static,
    ),
);
const canDeletePackage = computed(() => Boolean(canUnload.value && marketEntry.value));

function onSwitchChange(value: string | number | boolean) {
  emit("toggle", Boolean(value));
}
</script>

<style scoped>
.plugin-detail-panel {
  flex: 1;
  min-width: 0;
  overflow: auto;
  padding: 24px 28px;
}
.detail-header {
  margin-bottom: 18px;
}
.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.title-row h2 {
  margin: 0 4px 0 0;
  font-size: 22px;
  color: var(--el-text-color-primary);
}
.breadcrumb {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.parent-label {
  margin-right: 6px;
  color: var(--el-text-color-placeholder);
}
.description {
  margin: 10px 0 0;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}
.actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.switch-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-right: 6px;
}
.switch-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.expr-alert {
  margin-bottom: 16px;
}
.detail-descriptions {
  max-width: 860px;
}
.url-row {
  line-height: 1.8;
}
.ref-tag {
  margin: 0 6px 4px 0;
}
</style>
