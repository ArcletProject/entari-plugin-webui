<template>
  <div class="config-page">
    <el-aside width="220px" class="config-aside">
      <el-menu :default-active="current" @select="current = $event">
        <el-menu-item v-for="s in coreSections" :key="s" :index="s">{{ sectionLabel(s) }}</el-menu-item>
        <el-sub-menu index="plugins">
          <template #title>插件配置</template>
          <el-menu-item v-for="(_, key) in pluginSections" :key="key" :index="String(key)">{{ pluginSections[key] }}</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    <div class="config-main">
      <el-card>
        <template #header>{{ sectionLabel(current) }}</template>
        <DualConfigEditor v-if="schema" :schema="schema" v-model="data" :lang="'json'" />
        <el-empty v-else description="加载中…" />
        <div class="actions">
          <el-button type="primary" @click="save">保存</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { ElMessage } from "element-plus";
import api from "@/api/client";
import DualConfigEditor from "@/components/config/DualConfigEditor.vue";

const coreSections = ["basic", "adapters", "plugins"];
const pluginSections = ref<Record<string, string>>({});
const current = ref("basic");
const schema = ref<any>(null);
const data = ref<any>({});

function sectionLabel(s: string) {
  const map: Record<string, string> = { basic: "基础配置", adapters: "适配器", plugins: "插件全局" };
  return map[s] || pluginSections.value[s] || s;
}

async function loadSections() {
  const r = await api.get("/api/config");
  pluginSections.value = r.data.plugin_sections || {};
}

async function loadSection(section: string) {
  schema.value = null;
  const [sr, dr] = await Promise.all([
    api.get(`/api/config/${section}/schema`),
    api.get(`/api/config/${section}`),
  ]);
  schema.value = sr.data.schema;
  data.value = dr.data.data ?? {};
}

async function save() {
  await api.put(`/api/config/${current.value}`, { data: data.value });
  ElMessage.success("已保存");
}

watch(current, loadSection, { immediate: true });
onMounted(loadSections);
</script>
<style scoped>
.config-page { display: flex; height: 100%; padding: 16px; gap: 16px; }
.config-aside { flex-shrink: 0; }
.config-main { flex: 1; min-width: 0; }
.actions { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
