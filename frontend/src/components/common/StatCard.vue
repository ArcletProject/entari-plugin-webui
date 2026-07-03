<template>
  <el-card
    shadow="hover"
    class="stat-card"
  >
    <div class="stat-value">
      {{ value }}
    </div>
    <div class="stat-label">
      {{ label }}
    </div>
  </el-card>
</template>
<script setup lang="ts">
defineProps<{ value: string | number; label: string }>();
</script>
<style scoped>
.stat-card { text-align: center; }
.stat-value { font-size: 28px; font-weight: bold; color: var(--el-color-primary); }
.stat-label { margin-top: 8px; color: var(--el-text-color-secondary); }
</style>
