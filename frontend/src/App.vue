<template>
  <OfflineOverlay />
  <component :is="layout">
    <keep-alive include="Chat,Logs">
      <RouterView />
    </keep-alive>
  </component>
</template>
<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import Default from "@/layouts/Default.vue";
import Blank from "@/layouts/Blank.vue";
import OfflineOverlay from "@/components/OfflineOverlay.vue";
import { useThemeStore } from "@/stores/theme";
import i18n from "@/i18n";
import api from "@/api/client";

const route = useRoute();
const layout = computed(() => (route.meta.layout === "blank" ? Blank : Default));
useThemeStore().init();

function expandFlatKeys(obj: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    const parts = key.split(".");
    let current = result;
    for (let i = 0; i < parts.length - 1; i++) {
      if (!current[parts[i]]) current[parts[i]] = {};
      current = current[parts[i]];
    }
    current[parts[parts.length - 1]] = value;
  }
  return result;
}

onMounted(async () => {
  try {
    const r = await api.get("/api/extensions/manifest");
    const extI18n = r.data.i18n;
    if (extI18n) {
      for (const [locale, messages] of Object.entries(extI18n)) {
        i18n.global.mergeLocaleMessage(locale, expandFlatKeys(messages as Record<string, unknown>));
      }
    }
  } catch {
    // manifest 加载失败不影响主功能
  }
});
</script>
