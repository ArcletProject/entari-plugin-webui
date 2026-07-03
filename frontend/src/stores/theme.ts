import { defineStore } from "pinia";
import { ref, watch } from "vue";

export const useThemeStore = defineStore("theme", () => {
  const mode = ref<"light" | "dark">((localStorage.getItem("webui_theme") as "light" | "dark") || "light");
  function init() {
    watch(mode, (v) => {
      localStorage.setItem("webui_theme", v);
      document.documentElement.classList.toggle("dark", v === "dark");
    }, { immediate: true });
  }
  function toggle() { mode.value = mode.value === "light" ? "dark" : "light"; }
  return { mode, init, toggle };
});
