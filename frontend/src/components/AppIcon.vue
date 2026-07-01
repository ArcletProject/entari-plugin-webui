<template><el-icon><component :is="comp" /></el-icon></template>
<script setup lang="ts">
import { computed } from "vue";
const props = defineProps<{ icon: string }>();
// phase-10：引入 @iconify/vue 或 element-plus 图标映射
const comp = computed(() => null);
</script>
