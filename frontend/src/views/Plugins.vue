<template>
  <div class="plugins-page">
    <PluginManagerSidebar
      :plugins="store.plugins"
      :selected-uid="store.selectedUid"
      :loading="store.loading"
      @select="onSelect"
      @refresh="onRefresh"
    />

    <div class="plugins-main">
      <div class="page-header">
        <div>
          <h1>插件管理</h1>
          <p>启用、禁用、卸载插件，或跳转到配置页编辑。</p>
        </div>
        <el-tag
          v-if="store.plugins.length"
          type="info"
          effect="plain"
        >
          共 {{ store.plugins.length }} 个
        </el-tag>
      </div>

      <el-alert
        v-if="store.error"
        :title="store.error"
        type="error"
        :closable="false"
        class="page-error"
      />

      <PluginDetailPanel
        :plugin="store.selectedPlugin"
        :detail="store.detail"
        :pending="store.actionPending"
        @toggle="onToggle"
        @reload="store.reload"
        @unload="onUnload"
        @uninstall="onUninstall"
        @load="onLoad"
        @config="onConfig"
        @detail="onDetail"
      />

      <InstallProgress
        :task-id="store.taskId"
        @done="onTaskDone"
      />
    </div>

    <el-dialog
      v-model="detailOpen"
      title="插件详情"
      width="760px"
      destroy-on-close
    >
      <PluginDetailModal
        v-if="detailTarget"
        :plugin="detailTarget"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import InstallProgress from "@/components/market/InstallProgress.vue";
import PluginDetailModal from "@/components/plugins/PluginDetailModal.vue";
import PluginDetailPanel from "@/components/plugins/PluginDetailPanel.vue";
import PluginManagerSidebar from "@/components/plugins/PluginManagerSidebar.vue";
import { usePluginDisplayMode } from "@/composables/usePluginDisplayMode";
import { usePluginsStore, type ManagedPlugin } from "@/stores/plugins";
import {
  buildPluginTree,
  filterPluginTree,
  type PluginType,
} from "@/utils/plugin-tree";

type TreePlugin = ManagedPlugin & { id: string };

const store = usePluginsStore();
const route = useRoute();
const router = useRouter();
const { mode } = usePluginDisplayMode();
const detailOpen = ref(false);

const loadedPlugins = computed<TreePlugin[]>(() =>
  store.plugins.filter((p): p is TreePlugin => !p.unloaded && typeof p.id === "string"),
);

const visibleGroups = computed(() =>
  filterPluginTree(buildPluginTree(loadedPlugins.value), mode.value),
);

function firstVisibleUid(): string | undefined {
  const order: PluginType[] = ["built-in", "local", "common", "rootless"];
  for (const type of order) {
    const node = visibleGroups.value[type][0];
    if (node) return node.plugin.uid;
  }
  return undefined;
}

type DetailTarget = {
  id: string;
  version?: string;
  license?: string;
  authors?: string | string[];
  description?: string;
  urls?: Record<string, string> | string[];
  references?: string[];
  referents?: string[];
  readme?: string;
};

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function asStringList(value: unknown): string[] | undefined {
  return Array.isArray(value) ? value.map(String) : undefined;
}

const detailTarget = computed<DetailTarget | null>(() => {
  const plugin = store.selectedPlugin;
  if (!plugin) return null;
  const detail = store.detail ?? {};
  const authors = detail.authors;
  const urls = detail.urls;
  return {
    id: String(detail.id ?? plugin.id ?? plugin.uid),
    version: asString(detail.version) ?? plugin.version,
    license: asString(detail.license),
    authors:
      typeof authors === "string" || Array.isArray(authors)
        ? (authors as string | string[])
        : undefined,
    description: asString(detail.description) ?? plugin.description,
    urls:
      urls && typeof urls === "object"
        ? (urls as Record<string, string> | string[])
        : undefined,
    references: asStringList(detail.references),
    referents: asStringList(detail.referents),
    readme: asString(detail.readme),
  };
});

async function onSelect(uid: string) {
  await store.select(uid);
}

async function onRefresh() {
  await store.loadAll();
  if (!store.selectedPlugin) {
    const uid = firstVisibleUid();
    if (uid) await store.select(uid);
  }
}

async function onToggle(enable: boolean) {
  const plugin = store.selectedPlugin;
  if (!plugin) return;
  if (!enable && plugin.disable_expr) {
    try {
      await ElMessageBox.confirm(
        "该插件使用条件禁用表达式，手动切换会覆盖它。是否继续？",
        "条件禁用",
        { type: "warning" },
      );
    } catch {
      return;
    }
  }
  await store.toggle(enable);
}

async function onUnload() {
  const plugin = store.selectedPlugin;
  if (!plugin) return;
  const referents = Array.isArray(store.detail?.referents)
    ? (store.detail?.referents as string[])
    : [];
  const suffix = referents.length
    ? `\n依赖它的插件会被 entari 一并禁用：${referents.join("、")}`
    : "";
  try {
    await ElMessageBox.confirm(
      `确定卸载「${plugin.name}」吗？配置会保留为 ?${plugin.id ?? plugin.key ?? plugin.uid}。${suffix}`,
      "卸载插件",
      { type: "warning" },
    );
  } catch {
    return;
  }
  await store.unload();
}

async function onUninstall() {
  const plugin = store.selectedPlugin;
  if (!plugin) return;
  try {
    await ElMessageBox.confirm(
      `先卸载「${plugin.name}」，再从当前环境删除安装包。插件配置会保留为 ?${plugin.id ?? plugin.key ?? plugin.uid}。是否继续？`,
      "卸载并删除包",
      { type: "warning", confirmButtonText: "卸载并删除" },
    );
  } catch {
    return;
  }
  await store.uninstall();
}

async function onLoad() {
  const plugin = store.selectedPlugin;
  if (!plugin) return;
  const key = plugin.key ?? plugin.uid.replace(/^\?/, "");
  await store.load(key);
}

function onConfig() {
  const plugin = store.selectedPlugin;
  if (!plugin?.id) return;
  router.push({ path: "/settings", query: { section: `plugins:${plugin.id}` } });
}

async function onDetail() {
  await store.refreshDetail();
  detailOpen.value = true;
}

async function onTaskDone(success: boolean) {
  if (!success) {
    ElMessage.error("删除安装包失败，插件已卸载，配置仍保留");
  }
  store.taskId = undefined;
  await store.loadAll();
}

onMounted(async () => {
  await store.loadAll();
  const queryUid = typeof route.query.plugin === "string" ? route.query.plugin : "";
  if (queryUid && store.plugins.some((p) => p.uid === queryUid)) {
    await store.select(queryUid);
    return;
  }
  const uid = firstVisibleUid();
  if (uid) await store.select(uid);
});

watch(
  () => store.selectedUid,
  (uid) => {
    const current = typeof route.query.plugin === "string" ? route.query.plugin : "";
    if (uid === current) return;
    router.replace({ query: { ...route.query, plugin: uid || undefined } });
  },
);

watch(
  () => route.query.plugin,
  async (uid) => {
    if (typeof uid !== "string" || !uid || uid === store.selectedUid) return;
    if (store.plugins.some((p) => p.uid === uid)) await store.select(uid);
  },
);
</script>

<style scoped>
.plugins-page {
  display: flex;
  height: 100%;
  min-height: 0;
  background: var(--el-bg-color);
}
.plugins-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: auto;
  padding: 24px 28px;
}
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}
.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: var(--el-text-color-primary);
}
.page-header p {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.page-error {
  margin-bottom: 16px;
}
@media (max-width: 900px) {
  .plugins-page {
    flex-direction: column;
  }
  .plugins-page :deep(.plugin-manager-sidebar) {
    width: 100%;
    max-height: 42vh;
    border-right: none;
    border-bottom: 1px solid var(--el-border-color);
  }
  .plugins-main {
    padding: 16px;
  }
}
</style>
