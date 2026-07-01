<template>
  <OfflineOverlay />
  <RouterView />
</template>
<script setup lang="ts">
import OfflineOverlay from "@/components/OfflineOverlay.vue";
import { useThemeStore } from "@/stores/theme";
const theme = useThemeStore();
theme.init();
</script>
