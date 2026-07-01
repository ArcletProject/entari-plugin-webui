<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h2>仪表盘</h2>
      <el-tag :type="modeTag.type as any" size="large">{{ modeTag.label }}</el-tag>
    </div>
    <div class="stats-row">
      <StatCard v-for="s in stats" :key="s.label" :value="s.value" :label="s.label" />
    </div>
    <el-card class="chart-card">
      <template #header>近 7 日消息量</template>
      <v-chart class="chart" :option="chartOption" autoresize />
    </el-card>
    <div class="quick-actions">
      <el-button @click="$router.push('/plugins')">插件管理</el-button>
      <el-button @click="$router.push('/config')">配置管理</el-button>
      <el-button @click="$router.push('/logs')">实时日志</el-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import api from "@/api/client";
import StatCard from "@/components/common/StatCard.vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const data = ref<any>({});
const stats = computed(() => [
  { value: data.value.today_messages ?? 0, label: "今日消息" },
  { value: data.value.total_messages ?? 0, label: "累计消息" },
  { value: `${data.value.plugins_enabled ?? 0}/${data.value.plugins_total ?? 0}`, label: "启用/插件" },
  { value: data.value.runtime_minutes ?? 0, label: "运行分钟" },
]);
const modeTag = computed(() => ({
  type: auth.localMode ? "success" : "primary",
  label: auth.localMode ? "本地模式" : "远程模式",
}));
const chartOption = computed(() => ({
  xAxis: { type: "category", data: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"] },
  yAxis: { type: "value" },
  series: [{ data: data.value.week_messages ?? [0, 0, 0, 0, 0, 0, 0], type: "line", smooth: true }],
  tooltip: { trigger: "axis" },
}));

onMounted(async () => {
  const r = await api.get("/api/stats");
  data.value = r.data;
});
</script>
<style scoped>
.dashboard-page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.chart-card { margin-bottom: 16px; }
.chart { height: 360px; }
.quick-actions { display: flex; gap: 12px; }
</style>
