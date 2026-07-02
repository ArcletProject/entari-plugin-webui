import { defineStore } from "pinia";
import { ref, computed } from "vue";
import api from "@/api/client";

export const META_KEYS = ["$prefix", "$files", "$prelude", "$disable", "$priority", "$filter", "$optional"];

const META_LABELS: Record<string, string> = {
  "$prefix": "前缀配置",
  "$files": "配置文件列表",
  "$prelude": "预加载插件",
  "$disable": "禁用条件",
  "$priority": "加载优先级",
  "$filter": "过滤表达式",
  "$optional": "是否可选",
};

export interface PluginInfo {
  id: string;
  name: string;
  description?: string;
  version?: string;
  enabled: boolean;
  is_static: boolean;
  configurable: boolean;
}

function patchTitles(properties: Record<string, any>) {
  const out: Record<string, any> = {};
  for (const [key, prop] of Object.entries(properties)) {
    const label = META_LABELS[key];
    out[key] = label ? { ...prop, title: label } : { ...prop };
  }
  return out;
}

function splitSchema(schema: any, splitMeta: boolean) {
  const properties = schema?.properties || {};
  if (!splitMeta) {
    return { metaSchema: null, configSchema: schema ? { ...schema, properties: patchTitles(properties) } : null };
  }
  const metaProps: Record<string, any> = {};
  const configProps: Record<string, any> = {};
  for (const [key, value] of Object.entries(properties)) {
    if (META_KEYS.includes(key)) metaProps[key] = value;
    else configProps[key] = value;
  }
  const metaSchema = Object.keys(metaProps).length
    ? { ...schema, properties: patchTitles(metaProps), required: (schema.required || []).filter((k: string) => META_KEYS.includes(k)) }
    : null;
  const configSchema = Object.keys(configProps).length
    ? { ...schema, properties: configProps, required: (schema.required || []).filter((k: string) => !META_KEYS.includes(k)) }
    : null;
  return { metaSchema, configSchema };
}

function splitData(data: any, splitMeta: boolean) {
  const metaData: Record<string, any> = {};
  const configData: Record<string, any> = {};
  if (splitMeta && data && typeof data === "object" && !Array.isArray(data)) {
    for (const [key, value] of Object.entries(data)) {
      if (META_KEYS.includes(key)) metaData[key] = value;
      else configData[key] = value;
    }
  } else {
    Object.assign(configData, data ?? {});
  }
  return { metaData, configData };
}

export const useSettingsStore = defineStore("settings", () => {
  const pluginList = ref<PluginInfo[]>([]);
  const pluginRawMap = ref<Record<string, any>>({});
  const currentSection = ref<string>("basic");
  const rawSchema = ref<any>(null);
  const metaSchema = ref<any>(null);
  const configSchema = ref<any>(null);
  const metaData = ref<Record<string, any>>({});
  const configData = ref<any>({});
  const loading = ref(false);
  const isDirty = ref(false);
  const savePending = ref(false);
  const error = ref<string>("");

  const isPluginSection = computed(() => currentSection.value.startsWith("plugins:"));
  const pluginId = computed(() => (isPluginSection.value ? currentSection.value.slice(8) : ""));
  const currentPlugin = computed(() => pluginList.value.find((p) => p.id === pluginId.value));

  async function loadPlugins() {
    try {
      const r = await api.get("/api/plugins");
      const raw = r.data.data || [];
      pluginList.value = raw.map((p: any) => ({
        id: p.id,
        name: p.name,
        description: p.description,
        version: p.version,
        enabled: p.enabled,
        is_static: p.is_static,
        configurable: p.configurable,
      }));
      pluginRawMap.value = {};
      for (const p of raw) {
        pluginRawMap.value[p.id] = p;
      }
    } catch (e: any) {
      error.value = "加载插件列表失败";
    }
  }

  async function loadSection(section: string) {
    loading.value = true;
    error.value = "";
    currentSection.value = section;
    try {
      const [schemaR, dataR] = await Promise.all([
        api.get(`/api/config/${section}/schema`),
        api.get(`/api/config/${section}`),
      ]);
      rawSchema.value = schemaR.data.schema;
      const split = section.startsWith("plugins:");
      const { metaSchema: ms, configSchema: cs } = splitSchema(rawSchema.value, split);
      metaSchema.value = ms;
      configSchema.value = cs;
      const rawData = dataR.data.data ?? {};
      const { metaData: md, configData: cd } = splitData(rawData, split);
      metaData.value = md;
      configData.value = cd;
      isDirty.value = false;
    } catch (e: any) {
      error.value = "加载配置失败";
      rawSchema.value = null;
      metaSchema.value = null;
      configSchema.value = null;
      metaData.value = {};
      configData.value = {};
    } finally {
      loading.value = false;
    }
  }

  function markDirty() {
    isDirty.value = true;
  }

  async function save() {
    savePending.value = true;
    error.value = "";
    const merged = { ...metaData.value, ...configData.value };
    try {
      if (isPluginSection.value) {
        await api.put(`/api/plugins/${pluginId.value}/config`, { config: merged });
      } else {
        await api.put(`/api/config/${currentSection.value}`, { data: merged });
      }
      isDirty.value = false;
      return true;
    } catch (e: any) {
      error.value = "保存失败";
      return false;
    } finally {
      savePending.value = false;
    }
  }

  async function togglePlugin(pluginId: string, enable: boolean) {
    await api.post(`/api/plugins/${pluginId}/toggle`, { enable });
    const p = pluginList.value.find((x) => x.id === pluginId);
    if (p) p.enabled = enable;
  }

  async function reloadPlugin(pluginId: string) {
    await api.post(`/api/plugins/${pluginId}/reload`);
  }

  return {
    pluginList,
    pluginRawMap,
    currentSection,
    metaSchema,
    configSchema,
    metaData,
    configData,
    loading,
    isDirty,
    savePending,
    error,
    isPluginSection,
    pluginId,
    currentPlugin,
    loadPlugins,
    loadSection,
    markDirty,
    save,
    togglePlugin,
    reloadPlugin,
  };
});
