<template>
  <el-overlay
    v-if="state === 'offline'"
    :z-index="3000"
  >
    <div class="offline-box">
      <el-icon size="48">
        <WarnTriangleFilled />
      </el-icon>
      <h2>{{ t("health.offline") }}</h2>
      <el-button
        type="primary"
        @click="reconnectNow()"
      >
        {{ t("health.retry") }}
      </el-button>
    </div>
  </el-overlay>
  <div
    v-else-if="state === 'reconnecting'"
    class="reconnecting-banner"
  >
    {{ t("health.reconnecting") }}
  </div>
</template>
<script setup lang="ts">
import { onMounted } from "vue";
import { useBackendHealth } from "@/composables/useBackendHealth";
import { WarnTriangleFilled } from "@element-plus/icons-vue";
import { useI18n } from "vue-i18n";
const { state, start, reconnectNow } = useBackendHealth();
const { t } = useI18n();
onMounted(() => { start(); });
</script>
<style scoped>
.offline-box { display:flex; flex-direction:column; align-items:center; gap:16px; color:#fff; }
.reconnecting-banner { position:fixed; top:0; left:0; right:0; background:var(--el-color-warning); color:#fff; text-align:center; padding:4px; z-index:2000; }
</style>
