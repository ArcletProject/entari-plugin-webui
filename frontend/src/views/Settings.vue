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
