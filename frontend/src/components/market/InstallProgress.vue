<template>
  <div
    v-if="taskId"
    class="install-progress"
  >
    <el-progress
      :percentage="percent"
      :status="status"
    />
    <div class="msg">
      {{ message }}
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from "vue";
import api from "@/api/client";
const props = defineProps<{ taskId?: string }>();
const emit = defineEmits<{ done: [success: boolean] }>();
const percent = ref(0);
const status = ref<"" | "success" | "exception">("");
const message = ref("");
let timer: number | null = null;
let count = 0;

watch(() => props.taskId, (id) => {
  if (timer) { clearInterval(timer); timer = null; }
  if (!id) { percent.value = 0; status.value = ""; message.value = ""; return; }
  percent.value = 0; status.value = ""; message.value = ""; count = 0;
  timer = window.setInterval(async () => {
    count += 1;
    if (count > 60) { clearInterval(timer!); timer = null; status.value = "exception"; message.value = "超时"; emit("done", false); return; }
    try {
      const r = await api.get(`/api/market/tasks/${id}`);
      const t = r.data;
      percent.value = t.percent ?? 0;
      message.value = t.message || `${t.action} ${t.pip_name}`;
      if (t.status === "success" || t.status === "failed") {
        const ok = t.status === "success";
        status.value = ok ? "success" : "exception";
        clearInterval(timer!); timer = null;
        setTimeout(() => emit("done", ok), ok ? 1000 : 0);
      }
    } catch { /* ignore */ }
  }, 1000);
}, { immediate: true });
</script>
<style scoped>
.install-progress { margin-top: 16px; }
.msg { margin-top: 8px; font-size: 12px; color: var(--el-text-color-secondary); }
</style>
