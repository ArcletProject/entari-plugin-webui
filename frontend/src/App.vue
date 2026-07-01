<template>
  <OfflineOverlay />
  <component :is="layout"><RouterView /></component>
</template>
<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import Default from "@/layouts/Default.vue";
import Blank from "@/layouts/Blank.vue";
import OfflineOverlay from "@/components/OfflineOverlay.vue";
import { useThemeStore } from "@/stores/theme";
const route = useRoute();
const layout = computed(() => (route.meta.layout === "blank" ? Blank : Default));
useThemeStore().init();
</script>
