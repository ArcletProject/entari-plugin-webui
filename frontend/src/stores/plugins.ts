import { defineStore } from "pinia";
import { computed, ref } from "vue";
import api from "@/api/client";
import type { PluginInfo } from "@/stores/settings";
import { mergePluginSources } from "@/utils/plugin-list";

export type PluginState = "enabled" | "disabled" | "unavailable" | "unloaded";

export interface ManagedPlugin extends Omit<PluginInfo, "id"> {
  id: string | null;
  uid: string;
  key?: string;
  unloaded?: boolean;
  display_key?: string;
  market?: { name: string; pip_name: string } | null;
  builtin_name?: string;
  builtin_title?: string;
  builtin_description?: string;
  has_metadata: boolean;
  has_config_schema: boolean;
  can_unload: boolean;
  state: PluginState;
  disable_expr: string | null;
  parent_enabled: boolean | null;
}

export const usePluginsStore = defineStore("plugins", () => {
  const plugins = ref<ManagedPlugin[]>([]);
  const selectedUid = ref("");
  const detail = ref<Record<string, unknown> | null>(null);
  const loading = ref(false);
  const actionPending = ref(false);
  const taskId = ref<string | undefined>(undefined);
  const error = ref("");

  const selectedPlugin = computed(
    () => plugins.value.find((p) => p.uid === selectedUid.value) ?? null,
  );

  async function loadAll() {
    loading.value = true;
    error.value = "";
    try {
      const [loadedR, unloadedR, builtinsR] = await Promise.all([
        api.get("/api/plugins"),
        api.get("/api/plugins/unloaded"),
        api.get("/api/market/builtins"),
      ]);
      plugins.value = mergePluginSources(
        loadedR.data.data || [],
        unloadedR.data.plugins || [],
        builtinsR.data.data || [],
      );
      if (selectedUid.value && !plugins.value.some((p) => p.uid === selectedUid.value)) {
        selectedUid.value = "";
        detail.value = null;
      }
    } catch {
      error.value = "加载插件列表失败";
    } finally {
      loading.value = false;
    }
  }

  async function refreshDetail() {
    const plugin = selectedPlugin.value;
    if (!plugin) {
      detail.value = null;
      return;
    }
    if (plugin.unloaded || !plugin.id || (plugin.state === "unavailable" && plugin.builtin_name)) {
      detail.value = { ...plugin };
      return;
    }
    try {
      const r = await api.get(`/api/plugins/${plugin.id}`);
      detail.value = r.data.data ?? { ...plugin };
    } catch {
      detail.value = { ...plugin };
      error.value = "加载插件详情失败";
    }
  }

  async function select(uid: string) {
    selectedUid.value = uid;
    await refreshDetail();
  }

  async function load(key: string) {
    actionPending.value = true;
    error.value = "";
    try {
      const r = await api.post("/api/plugins/load", { key });
      const data = r.data.data as ManagedPlugin | undefined;
      await loadAll();
      const uid = data?.id ?? `?${key.replace(/^\?/, "")}`;
      if (plugins.value.some((p) => p.uid === uid)) await select(uid);
    } catch {
      error.value = "加载插件失败";
    } finally {
      actionPending.value = false;
    }
  }

  async function toggle(enable: boolean) {
    const plugin = selectedPlugin.value;
    if (!plugin) return;
    if (plugin.unloaded && plugin.key) {
      await load(plugin.key);
      return;
    }
    actionPending.value = true;
    error.value = "";
    try {
      if (plugin.builtin_name && plugin.state === "unavailable") {
        await api.post(`/api/market/builtins/${plugin.builtin_name}/toggle`, { enable });
        await loadAll();
        const uid = plugin.id && plugins.value.some((p) => p.uid === plugin.id) ? plugin.id : plugin.uid;
        if (plugins.value.some((p) => p.uid === uid)) await select(uid);
        return;
      }
      if (!plugin.id) return;
      await api.post(`/api/plugins/${plugin.id}/toggle`, { enable });
      await loadAll();
      if (plugin.uid === selectedUid.value) await refreshDetail();
    } catch {
      error.value = "切换插件状态失败";
    } finally {
      actionPending.value = false;
    }
  }

  async function reload() {
    const plugin = selectedPlugin.value;
    if (!plugin?.id) return;
    actionPending.value = true;
    error.value = "";
    try {
      await api.post(`/api/plugins/${plugin.id}/reload`);
      await loadAll();
      await refreshDetail();
    } catch {
      error.value = "重载插件失败";
    } finally {
      actionPending.value = false;
    }
  }

  async function unload() {
    const plugin = selectedPlugin.value;
    if (!plugin?.id) return;
    actionPending.value = true;
    error.value = "";
    try {
      const r = await api.post(`/api/plugins/${plugin.id}/unload`);
      const data = r.data.data as Record<string, unknown> | undefined;
      const key = String(data?.config_key ?? data?.key ?? plugin.key ?? plugin.id);
      await loadAll();
      const uid = `?${key.replace(/^\?/, "")}`;
      if (plugins.value.some((p) => p.uid === uid)) await select(uid);
    } catch {
      error.value = "卸载插件失败";
    } finally {
      actionPending.value = false;
    }
  }

  async function uninstall() {
    const plugin = selectedPlugin.value;
    if (!plugin?.id) return;
    actionPending.value = true;
    error.value = "";
    try {
      const r = await api.post(`/api/plugins/${plugin.id}/uninstall`);
      taskId.value = r.data.task_id as string | undefined;
      await loadAll();
      const key = plugin.key ?? plugin.id;
      const uid = `?${key.replace(/^\?/, "")}`;
      if (plugins.value.some((p) => p.uid === uid)) await select(uid);
    } catch {
      error.value = "卸载插件包失败";
    } finally {
      actionPending.value = false;
    }
  }

  return {
    plugins,
    selectedUid,
    detail,
    loading,
    actionPending,
    taskId,
    error,
    selectedPlugin,
    loadAll,
    select,
    toggle,
    reload,
    unload,
    load,
    uninstall,
    refreshDetail,
  };
});
