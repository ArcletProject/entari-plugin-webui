<template>
  <div class="settings-sidebar">
    <el-input
      v-model="keyword"
      placeholder="搜索插件"
      clearable
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
      <div class="group">
        <div class="group-title">
          根基插件
        </div>
        <div
          v-for="p in filteredRootlessPlugins"
          :key="p.id"
          :class="['menu-item', { active: store.currentSection === `plugins:${p.id}` }]"
          @click="select(`plugins:${p.id}`)"
        >
          <span class="name">{{ p.name }}</span>
          <el-tag
            v-if="!p.enabled"
            type="info"
            size="small"
            class="status"
          >
            已停用
          </el-tag>
        </div>
      </div>
      <div class="group">
        <div class="group-title">
          内建插件
        </div>
        <div
          v-for="p in filteredBuiltInPlugins"
          :key="p.id"
          :class="['menu-item', { active: store.currentSection === `plugins:${p.id}` }]"
          @click="select(`plugins:${p.id}`)"
        >
          <span class="name">{{ p.name }}</span>
          <el-tag
            v-if="!p.enabled"
            type="info"
            size="small"
            class="status"
          >
            已停用
          </el-tag>
        </div>
      </div>
      <div class="group">
        <div class="group-title">
          本地插件
        </div>
        <div
          v-for="p in filteredLocalPlugins"
          :key="p.id"
          :class="['menu-item', { active: store.currentSection === `plugins:${p.id}` }]"
          @click="select(`plugins:${p.id}`)"
        >
          <span class="name">{{ p.name }}</span>
          <el-tag
            v-if="!p.enabled"
            type="info"
            size="small"
            class="status"
          >
            已停用
          </el-tag>
        </div>
      </div>
      <div class="group">
        <div class="group-title">
          常规插件
        </div>
        <div
          v-for="p in filteredCommonPlugins"
          :key="p.id"
          :class="['menu-item', { active: store.currentSection === `plugins:${p.id}` }]"
          @click="select(`plugins:${p.id}`)"
        >
          <span class="name">{{ p.name }}</span>
          <el-tag
            v-if="!p.enabled"
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
import { ref, computed } from "vue";
import { useSettingsStore } from "@/stores/settings";

const store = useSettingsStore();
const keyword = ref("");

function filterByType(type: "rootless" | "built-in" | "local" | "common") {
  const list = store.pluginList.filter((p) => p.type === type);
  if (!keyword.value) return list;
  const q = keyword.value.toLowerCase();
  return list.filter((p) => p.name.toLowerCase().includes(q));
}

const filteredRootlessPlugins = computed(() => filterByType("rootless"));
const filteredBuiltInPlugins = computed(() => filterByType("built-in"));
const filteredLocalPlugins = computed(() => filterByType("local"));
const filteredCommonPlugins = computed(() => filterByType("common"));

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
