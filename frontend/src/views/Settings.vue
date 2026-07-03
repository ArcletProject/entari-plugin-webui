<template>
  <div class="settings-page">
    <SettingsSidebar />
    <div class="settings-main">
      <el-skeleton
        v-if="store.loading"
        :rows="10"
        animated
      />
      <template v-else>
        <PluginHeader
          v-if="store.currentPlugin"
          :plugin="store.currentPlugin"
          @toggle="(v) => onToggle(v)"
          @reload="onReload"
          @detail="showDetail"
        />
        <div
          v-else
          class="section-header"
        >
          <h3>{{ sectionTitle }}</h3>
        </div>

        <el-alert
          v-if="store.error"
          :title="store.error"
          type="error"
          :closable="false"
          class="mb-4"
        />

        <div class="actions">
          <el-button
            type="primary"
            :loading="store.savePending"
            @click="save"
          >
            <AppIcon
              icon="mdi:content-save"
              style="margin-right: 4px"
            />
            保存
          </el-button>
        </div>

        <MetaSettings
          v-if="store.metaSchema"
          v-model="store.metaData"
          :schema="store.metaSchema"
          @update:model-value="store.markDirty"
        />

        <el-card v-if="store.configSchema">
          <template #header>
            <div
              class="card-header collapsible"
              @click="configOpen = !configOpen"
            >
              <span>配置</span>
              <el-icon :class="{ 'is-reverse': configOpen }">
                <ArrowUpBold />
              </el-icon>
            </div>
          </template>
          <div v-show="configOpen">
            <DualConfigEditor
              :key="store.currentSection"
              v-model="store.configData"
              :schema="store.configSchema"
              lang="json"
              @update:model-value="store.markDirty"
            />
          </div>
        </el-card>

        <el-empty
          v-if="!store.metaSchema && !store.configSchema && !store.loading"
          description="无配置项"
        />
      </template>
    </div>

    <el-dialog
      v-model="detailVisible"
      width="600"
      :title="detailPlugin?.name"
    >
      <PluginDetailModal
        v-if="detailPlugin"
        :plugin="detailPlugin"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { useSettingsStore } from "@/stores/settings";
import SettingsSidebar from "@/components/settings/SettingsSidebar.vue";
import PluginHeader from "@/components/settings/PluginHeader.vue";
import MetaSettings from "@/components/settings/MetaSettings.vue";
import DualConfigEditor from "@/components/config/DualConfigEditor.vue";
import PluginDetailModal from "@/components/plugins/PluginDetailModal.vue";
import AppIcon from "@/components/AppIcon.vue";

defineOptions({ name: "Settings" });

const route = useRoute();
const store = useSettingsStore();
interface PluginDetail {
  id: string;
  name?: string;
  version?: string;
  license?: string;
  description?: string;
  authors?: string | string[];
  urls?: Record<string, string> | string[];
  references?: string[];
  referents?: string[];
  readme?: string;
}
const detailPlugin = ref<PluginDetail | null>(null);
const detailVisible = computed({ get: () => !!detailPlugin.value, set: (v) => { if (!v) detailPlugin.value = null; } });
const configOpen = ref(true);

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

function showDetail() {
  detailPlugin.value = store.pluginRawMap[store.pluginId] as PluginDetail;
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
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}
.mb-4 {
  margin-bottom: 16px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.collapsible {
  cursor: pointer;
  user-select: none;
}
.el-icon.is-reverse {
  transform: rotate(180deg);
}
</style>
