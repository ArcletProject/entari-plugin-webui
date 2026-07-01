<template>
  <div class="plugins-page">
    <div class="toolbar">
      <el-input v-model="search" placeholder="搜索" style="width:240px" clearable />
      <el-switch v-model="caseSensitive" active-text="大小写敏感" />
    </div>
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
    <el-dialog v-model="detailVisible" width="600" :title="detail?.name">
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
const caseSensitive = ref(false);
const filtered = computed(() => {
  if (!search.value) return list.value;
  const q = caseSensitive.value ? search.value : search.value.toLowerCase();
  return list.value.filter((p) => {
    const name = caseSensitive.value ? p.name : String(p.name || "").toLowerCase();
    return name.includes(q);
  });
});
const detail = ref<any>(null);
const detailVisible = computed({ get: () => !!detail.value, set: (v) => { if (!v) detail.value = null; } });

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
  const r = await api.get(`/api/config/plugins:${row.id}/schema`);
  drawerSchema.value = r.data.schema;
  drawerOpen.value = true;
}
async function saveConfig() {
  await api.put(`/api/plugins/${current.value.id}/config`, { config: drawerData.value });
  ElMessage.success("已保存"); drawerOpen.value = false; load();
}
onMounted(load);
</script>
<style scoped>
.plugins-page { padding: 16px; }
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; }
</style>
