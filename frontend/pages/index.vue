<template>
  <div class="dashboard">
    <n-grid :cols="4" :x-gap="16" :y-gap="16">
      <!-- 统计卡片 -->
      <n-gi>
        <n-card>
          <n-statistic label="今日消息" :value="stats.today_messages" />
        </n-card>
      </n-gi>

      <n-gi>
        <n-card>
          <n-statistic label="总消息数" :value="stats.total_messages" />
        </n-card>
      </n-gi>

      <n-gi>
        <n-card>
          <n-statistic label="插件状态">
            <template #default>
              <n-text type="success">{{ stats.plugins_enabled }}</n-text>
              <n-text depth="3"> / {{ stats.plugins_total }}</n-text>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>

      <n-gi>
        <n-card>
          <n-statistic label="运行时长" :value="formatRuntime(stats.runtime_minutes)" />
        </n-card>
      </n-gi>

      <!-- 周消息图表 -->
      <n-gi :span="4">
        <n-card title="本周消息趋势">
          <v-chart :option="chartOption" style="height: 300px" autoresize />
        </n-card>
      </n-gi>

      <!-- 快捷操作 -->
      <n-gi :span="2">
        <n-card title="快捷操作">
          <n-space>
            <n-button @click="$router.push('/plugins')">
              <template #icon>
                <Icon name="mdi:puzzle" />
              </template>
              插件管理
            </n-button>
            <n-button @click="$router.push('/config')">
              <template #icon>
                <Icon name="mdi:cog" />
              </template>
              配置管理
            </n-button>
            <n-button @click="$router.push('/logs')">
              <template #icon>
                <Icon name="mdi:console" />
              </template>
              查看日志
            </n-button>
          </n-space>
        </n-card>
      </n-gi>

      <!-- 系统信息 -->
      <n-gi :span="2">
        <n-card title="系统信息">
          <n-descriptions :column="1">
            <n-descriptions-item label="WebUI 版本">
              0.2.0
            </n-descriptions-item>
            <n-descriptions-item label="启动时间">
              {{ stats.start_time || '-' }}
            </n-descriptions-item>
            <n-descriptions-item label="认证模式">
              <n-tag :type="auth.localMode.value ? 'success' : 'warning'">
                {{ auth.localMode.value ? '本地模式' : '远程模式' }}
              </n-tag>
            </n-descriptions-item>
          </n-descriptions>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'

// 注册 ECharts 组件
use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const api = useApi()
const auth = useAuth()

// 统计数据
const stats = ref({
  today_messages: 0,
  total_messages: 0,
  week_messages: [0, 0, 0, 0, 0, 0, 0],
  plugins_enabled: 0,
  plugins_total: 0,
  runtime_minutes: 0,
  start_time: '',
})

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await api.get<any>('/stats')
    if (response.success) {
      stats.value = {
        ...stats.value,
        ...response,
      }
    }
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

// 格式化运行时长
const formatRuntime = (minutes: number): string => {
  if (minutes < 60) {
    return `${minutes} 分钟`
  }
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours < 24) {
    return `${hours} 小时 ${mins} 分钟`
  }
  const days = Math.floor(hours / 24)
  const hrs = hours % 24
  return `${days} 天 ${hrs} 小时`
}

// 图表配置
const chartOption = computed(() => {
  const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

  return {
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: weekDays,
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: '消息数',
        type: 'line',
        data: stats.value.week_messages,
        smooth: true,
        areaStyle: {
          opacity: 0.3,
        },
      },
    ],
  }
})

// 初始化
onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
