<template>
  <div class="settings-sidebar">
    <el-input
      v-model="keyword"
      placeholder="搜索插件"
      clearable
    />
    <PluginDisplayFilter
      v-model="mode"
      class="display-filter"
    />
    <el-scrollbar class="menu-scroll">
      <div class="group">
        <div class="group-title">
          基础配置
        </div>
        <div
          :class="['menu-item', { active: store.currentSection === 'basic' }]"
          @click="select('basic')"
        >
          基础配置
        </div>
        <div
          :class="['menu-item', { active: store.currentSection === 'plugins' }]"
          @click="select('plugins')"
        >
          插件全局
        </div>
      </div>
      <div class="group">
        <div class="group-title">
          适配器
        </div>
        <div
          :class="['menu-item', { active: store.currentSection === 'adapters' }]"
          @click="select('adapters')"
        >
          适配器
        </div>
      </div>
      <div
        v-for="group in pluginGroups"
        :key="group.type"
        class="group"
      >
        <div class="group-title">
          {{ group.title }}
        </div>
        <div
          v-for="item in group.items"
          :key="item.plugin.id"
          :class="['menu-item', { active: store.currentSection === `plugins:${item.plugin.id}` }]"
          :style="{ paddingLeft: `${12 + item.depth * 16}px` }"
          @click="select(`plugins:${item.plugin.id}`)"
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
            v-if="!item.plugin.enabled"
            type="info"
            size="small"
            class="status"
          >
            已停用
          </el-tag>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { ArrowRight } from "@element-plus/icons-vue";
import { useSettingsStore, type PluginInfo } from "@/stores/settings";
import PluginDisplayFilter from "@/components/plugins/PluginDisplayFilter.vue";
import { usePluginDisplayMode } from "@/composables/usePluginDisplayMode";
import {
  buildPluginTree,
  filterPluginTree,
  flattenPluginTree,
  type PluginTreeNode,
} from "@/utils/plugin-tree";

const store = useSettingsStore();
const { mode } = usePluginDisplayMode();
const keyword = ref("");
const collapsed = ref<Set<string>>(new Set());

const TYPE_GROUPS = [
  { type: "rootless", title: "根基插件" },
  { type: "built-in", title: "内建插件" },
  { type: "local", title: "本地插件" },
  { type: "common", title: "常规插件" },
] as const;

// 搜索时重置折叠状态：命中的父插件默认展开，仍可手动折叠
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

const pluginTrees = computed(() => {
  const pinnedId = store.isPluginSection ? store.pluginId : undefined;
  return filterPluginTree(buildPluginTree<PluginInfo>(store.pluginList), mode.value, pinnedId);
});

function filterTree(nodes: PluginTreeNode<PluginInfo>[], q: string, ancestorMatched = false): PluginTreeNode<PluginInfo>[] {
  const out: PluginTreeNode<PluginInfo>[] = [];
  for (const node of nodes) {
    const matched = ancestorMatched || node.plugin.name.toLowerCase().includes(q);
    const children = filterTree(node.children, q, matched);
    if (matched || children.length) out.push({ plugin: node.plugin, children });
  }
  return out;
}

const pluginGroups = computed(() => {
  const q = keyword.value.trim().toLowerCase();
  return TYPE_GROUPS.map((group) => {
    const nodes = pluginTrees.value[group.type] ?? [];
    const filtered = q ? filterTree(nodes, q) : nodes;
    return { type: group.type, title: group.title, items: flattenPluginTree(filtered, isExpanded) };
  });
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
.display-filter {
  margin-top: 8px;
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
</style>
