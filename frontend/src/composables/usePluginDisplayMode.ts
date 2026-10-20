import { ref, watch } from "vue";
import type { PluginDisplayMode } from "@/utils/plugin-tree";

export const PLUGIN_DISPLAY_MODE_KEY = "webui.pluginDisplayMode";

function readMode(): PluginDisplayMode {
  if (typeof localStorage === "undefined") return "configured";
  const value = localStorage.getItem(PLUGIN_DISPLAY_MODE_KEY);
  if (value === "top" || value === "configured" || value === "all") return value;
  return "configured";
}

const mode = ref<PluginDisplayMode>(readMode());

watch(mode, (value) => {
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(PLUGIN_DISPLAY_MODE_KEY, value);
  }
});

export function usePluginDisplayMode(): { mode: typeof mode } {
  return { mode };
}
