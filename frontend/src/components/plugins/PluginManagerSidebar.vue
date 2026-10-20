<template>
  <div class="plugin-manager-sidebar">
    <div class="sidebar-controls">
      <el-input
        v-model="keyword"
        placeholder="搜索插件名、ID 或配置键"
        clearable
      />
      <PluginDisplayFilter
        v-model="mode"
        class="display-filter"
      />
      <el-button
        size="small"
        :loading="loading"
        @click="emit('refresh')"
      >
        刷新
      </el-button>
    </div>

    <el-scrollbar
      v-loading="loading"
      class="sidebar-scroll"
    >
      <template
        v-for="group in pluginGroups"
        :key="group.type"
      >
        <div
          v-if="group.items.length"
          class="group"
        >
          <div class="group-title">
            {{ group.title }}
          </div>
          <div
            v-for="item in group.items"
            :key="item.plugin.uid"
            :class="['menu-item', { active: item.plugin.uid === selectedUid }]"
            :style="{ paddingLeft: `${12 + item.depth * 16}px` }"
            :title="item.plugin.id || item.plugin.uid"
            @click="emit('select', item.plugin.uid)"
          >
            <span
              v-if="item.hasChildren"
              class="toggle"
              :class="{ expanded: isExpanded(item.plugin.id) }"
              @click.stop="toggleCollapse(item.plugin.id)"
            >
              <el-icon><ArrowRight /></el-icon>
            </span>
            <span
              v-else
              class="toggle-placeholder"
            />
            <span class="name">{{ item.plugin.name }}</span>
            <el-tag
              v-if="statusTag(item.plugin)"
              :type="statusTag(item.plugin)!.type"
              size="small"
              class="status"
            >
              {{ statusTag(item.plugin)!.label }}
            </el-tag>
          </div>
        </div>
      </template>

      <div class="group">
        <div class="group-title">
          已卸载
        </div>
        <div
          v-if="!unloadedItems.length"
          class="empty-hint"
        >
          暂无已卸载插件
        </div>
        <div
          v-for="item in unloadedItems"
          :key="item.uid"
          :class="['menu-item', { active: item.uid === selectedUid }]"
          :title="item.display_key || item.key"
          @click="emit('select', item.uid)"
        >
          <span class="toggle-placeholder" />
          <span class="name">{{ item.builtin_title || item.name || item.key }}</span>
          <el-tag
            size="small"
            type="info"
            class="status"
          >
            已卸载
          </el-tag>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ArrowRight } from "@element-plus/icons-vue";
import PluginDisplayFilter from "@/components/plugins/PluginDisplayFilter.vue";
import { usePluginDisplayMode } from "@/composables/usePluginDisplayMode";
import type { ManagedPlugin } from "@/stores/plugins";
import {
  buildPluginTree,
  filterPluginTree,
  flattenPluginTree,
  matchesPluginSearch,
  type PluginType,
  type PluginTreeNode,
} from "@/utils/plugin-tree";

const props = defineProps<{
  plugins: ManagedPlugin[];
  selectedUid?: string;
  loading?: boolean;
}>();

const emit = defineEmits<{
  select: [uid: string];
  refresh: [];
}>();

type TreePlugin = ManagedPlugin & { id: string };

const TYPE_GROUPS: { type: PluginType; title: string }[] = [
  { type: "rootless", title: "根基插件" },
  { type: "built-in", title: "内建插件" },
  { type: "local", title: "本地插件" },
  { type: "common", title: "常规插件" },
];

const { mode } = usePluginDisplayMode();
const keyword = ref("");
const collapsed = ref<Set<string>>(new Set());

const loadedPlugins = computed(() =>
  props.plugins.filter((p): p is TreePlugin => !p.unloaded && typeof p.id === "string"),
);

const unloadedItems = computed(() => {
  const q = keyword.value.trim().toLowerCase();
  return props.plugins
    .filter((p) => p.unloaded)
    .filter((p) => {
      return matchesPluginSearch(p, q);
    })
    .sort((a, b) => a.name.localeCompare(b.name));
});

const treeGroups = computed(() =>
  filterPluginTree(buildPluginTree(loadedPlugins.value), mode.value, props.selectedUid),
);

function filterNodes(nodes: PluginTreeNode<TreePlugin>[], q: string, ancestorMatched = false): PluginTreeNode<TreePlugin>[] {
  const out: PluginTreeNode<TreePlugin>[] = [];
  for (const node of nodes) {
    const selfMatched = ancestorMatched || matchesPluginSearch(node.plugin, q);
    const children = selfMatched ? node.children : filterNodes(node.children, q);
    if (selfMatched || children.length) {
      out.push({ plugin: node.plugin, children });
    }
  }
  return out;
}

const pluginGroups = computed(() => {
  const q = keyword.value.trim().toLowerCase();
  return TYPE_GROUPS.map((group) => {
    const nodes = q ? filterNodes(treeGroups.value[group.type], q) : treeGroups.value[group.type];
    return {
      type: group.type,
      title: group.title,
      items: flattenPluginTree(nodes, isExpanded),
    };
  });
});

function statusTag(plugin: TreePlugin): { label: string; type: "success" | "warning" | "info" | "danger" } | null {
  if (plugin.state === "disabled") return { label: "已禁用", type: "warning" };
  if (plugin.state === "unavailable") return { label: "不可用", type: "info" };
  return null;
}

watch(keyword, () => {
  collapsed.value = new Set();
});

function isExpanded(id: string) {
  return !collapsed.value.has(id);
}

function toggleCollapse(id: string) {
  const next = new Set(collapsed.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  collapsed.value = next;
}
</script>

<style scoped>
.plugin-manager-sidebar {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--el-border-color);
  min-height: 0;
}
.sidebar-controls {
  padding: 16px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.sidebar-controls .el-button {
  align-self: flex-start;
}
.display-filter {
  width: 100%;
}
.sidebar-scroll {
  flex: 1;
  min-height: 0;
  padding: 0 8px 16px;
}
.group {
  margin-bottom: 12px;
}
.group-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 13px;
  padding: 8px 12px;
}
.menu-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin: 2px 0;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  min-width: 0;
}
.menu-item:hover {
  background: var(--el-fill-color-light);
}
.menu-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.toggle,
.toggle-placeholder {
  width: 16px;
  height: 16px;
  margin-right: 4px;
  flex-shrink: 0;
}
.toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  border-radius: 4px;
}
.toggle:hover {
  color: var(--el-text-color-primary);
  background: var(--el-fill-color);
}
.toggle .el-icon {
  transition: transform 0.2s;
}
.toggle.expanded .el-icon {
  transform: rotate(90deg);
}
.name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.status {
  margin-left: 8px;
  flex-shrink: 0;
}
.empty-hint {
  padding: 6px 12px 10px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
