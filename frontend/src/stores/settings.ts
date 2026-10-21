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
  type: "rootless" | "built-in" | "local" | "common";
  enabled: boolean;
  is_static: boolean;
  configurable: boolean;
  parent?: string | null;
  has_metadata: boolean;
  has_config_schema: boolean;
  config_key?: string;
  can_unload: boolean;
  state: "enabled" | "disabled" | "unavailable" | "unloaded";
  disable_expr: string | null;
  parent_enabled: boolean | null;
}

function patchTitles(properties: Record<string, unknown>) {
  const out: Record<string, unknown> = {};
  for (const [key, prop] of Object.entries(properties)) {
    const label = META_LABELS[key];
    out[key] = label ? { ...(prop as Record<string, unknown>), title: label } : { ...(prop as Record<string, unknown>) };
  }
  return out;
}

function splitSchema(schema: Record<string, unknown> | null, splitMeta: boolean) {
  const properties = ((schema?.properties as Record<string, unknown> | undefined) || {});
  if (!splitMeta) {
    return { metaSchema: null, configSchema: schema ? { ...schema, properties: patchTitles(properties) } : null };
  }
  const metaProps: Record<string, unknown> = {};
  const configProps: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(properties)) {
    if (META_KEYS.includes(key)) metaProps[key] = value;
    else configProps[key] = value;
  }
  const metaSchema = Object.keys(metaProps).length
    ? { ...schema, properties: patchTitles(metaProps), required: ((schema?.required as string[] | undefined) || []).filter((k: string) => META_KEYS.includes(k)) }
    : null;
  const configSchema = Object.keys(configProps).length
    ? { ...schema, properties: configProps, required: ((schema?.required as string[] | undefined) || []).filter((k: string) => !META_KEYS.includes(k)) }
    : null;
  return { metaSchema, configSchema };
}

function splitData(data: unknown, splitMeta: boolean) {
  const metaData: Record<string, unknown> = {};
  const configData: Record<string, unknown> = {};
  if (splitMeta && data && typeof data === "object" && !Array.isArray(data)) {
    for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
      if (META_KEYS.includes(key)) metaData[key] = value;
      else configData[key] = value;
    }
  } else {
    Object.assign(configData, (data ?? {}) as Record<string, unknown>);
  }
  return { metaData, configData };
}

export const useSettingsStore = defineStore("settings", () => {
  const pluginList = ref<PluginInfo[]>([]);
  const pluginRawMap = ref<Record<string, unknown>>({});
  const currentSection = ref<string>("basic");
  const rawSchema = ref<Record<string, unknown> | null>(null);
  const metaSchema = ref<Record<string, unknown> | null>(null);
  const configSchema = ref<Record<string, unknown> | null>(null);
  const metaData = ref<Record<string, unknown>>({});
  const configData = ref<Record<string, unknown>>({});
  const loading = ref(false);
  const isDirty = ref(false);
  const savePending = ref(false);
  const error = ref<string>("");
  const etag = ref<string>("");

  interface SchemaCacheEntry { rawSchema: Record<string, unknown> | null; metaSchema: Record<string, unknown> | null; configSchema: Record<string, unknown> | null }
  const schemaCache = ref<Record<string, SchemaCacheEntry>>({});

  const isPluginSection = computed(() => currentSection.value.startsWith("plugins:"));
  const pluginId = computed(() => (isPluginSection.value ? currentSection.value.slice(8) : ""));
  const currentPlugin = computed(() => pluginList.value.find((p) => p.id === pluginId.value));

  async function loadPlugins() {
    try {
      const r = await api.get("/api/plugins");
      const raw = r.data.data || [];
      pluginList.value = raw.map((p: Record<string, unknown>) => ({
        id: p.id as string,
        name: p.name as string,
        description: p.description as string | undefined,
        version: p.version as string | undefined,
        type: (p.type as "rootless" | "built-in" | "local" | "common") || "common",
        enabled: p.enabled as boolean,
        is_static: p.is_static as boolean,
        configurable: p.configurable as boolean,
        parent: (p.parent as string | null | undefined) ?? null,
        has_metadata: !!p.has_metadata,
        has_config_schema: !!p.has_config_schema,
        config_key: p.config_key as string | undefined,
        can_unload: !!p.can_unload,
        state: (p.state as PluginInfo["state"]) || (p.enabled ? "enabled" : "unavailable"),
        disable_expr: (p.disable_expr as string | null | undefined) ?? null,
        parent_enabled: (p.parent_enabled as boolean | null | undefined) ?? null,
      }));
      pluginRawMap.value = {};
      for (const p of raw) {
        pluginRawMap.value[p.id] = p;
      }
    } catch {
      error.value = "加载插件列表失败";
    }
  }

  async function loadSection(section: string) {
    loading.value = true;
    error.value = "";
    currentSection.value = section;
    try {
      const split = section.startsWith("plugins:");
      let schemas: SchemaCacheEntry;
      const cached = schemaCache.value[section];
      if (cached) {
        schemas = cached;
      } else {
        const schemaR = await api.get(`/api/config/${section}/schema`);
        const { metaSchema: ms, configSchema: cs } = splitSchema(schemaR.data.schema, split);
        schemas = { rawSchema: schemaR.data.schema, metaSchema: ms, configSchema: cs };
        schemaCache.value[section] = schemas;
      }
      rawSchema.value = schemas.rawSchema;
      metaSchema.value = schemas.metaSchema;
      configSchema.value = schemas.configSchema;

      const dataR = await api.get(`/api/config/${section}`);
      const rawData = dataR.data.data ?? {};
      const { metaData: md, configData: cd } = splitData(rawData, split);
      metaData.value = md;
      configData.value = cd;
      etag.value = dataR.data.etag ?? "";
      isDirty.value = false;
    } catch {
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

  async function save(): Promise<{ success: boolean; message: string }> {
    savePending.value = true;
    error.value = "";
    if (!etag.value) {
      savePending.value = false;
      error.value = "配置尚未加载完成，请刷新后重试";
      return { success: false, message: error.value };
    }
    const merged = { ...metaData.value, ...configData.value };
    const headers = { "If-Match": etag.value };
    try {
      const r = isPluginSection.value
        ? await api.put(`/api/plugins/${pluginId.value}/config`, { config: merged }, { headers })
        : await api.put(`/api/config/${currentSection.value}`, { data: merged }, { headers });
      const payload = r.data ?? {};
      if (payload.etag) etag.value = payload.etag;
      const report = payload.apply;
      if (report && report.ok === false) {
        const details = (report.errors ?? [])
          .map((e: { plugin?: string; message?: string }) => `${e.plugin ?? "?"}: ${e.message ?? ""}`)
          .join("; ");
        error.value = `配置已写入，但应用失败${details ? `：${details}` : ""}`;
        return { success: false, message: error.value };
      }
      isDirty.value = false;
      return { success: true, message: payload.message || "设置已保存" };
    } catch (e) {
      const err = e as { response?: { status?: number; data?: { message?: string; etag?: string } } };
      const status = err.response?.status;
      if (status === 409) {
        // 不要更新 etag：保留旧版本，避免用户再次保存时用旧数据覆盖外部修改
        error.value = "配置已被外部修改，请刷新后重试";
      } else if (status === 428) {
        error.value = "缺少配置版本信息，请刷新后重试";
      } else {
        error.value = err.response?.data?.message || "保存失败";
      }
      return { success: false, message: error.value };
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
    etag,
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
