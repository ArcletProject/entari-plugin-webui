<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useInitData } from '@/stores/counter'

const initData = useInitData()
const chartRef = ref<HTMLDivElement>()

let chart: echarts.ECharts | null = null

const buildOption = (): echarts.EChartsOption => ({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: initData.weekLabels
    },
    yAxis: { type: 'value', name: '消息量' },
    series: [
        {
            name: '今日消息量',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            data: initData.weekMessages,
            areaStyle: { opacity: 0.25 }
        }
    ]
})

onMounted(async () => {
    await nextTick()
    chart = echarts.init(chartRef.value!)
    chart.setOption(buildOption())
    window.addEventListener('resize', () => chart?.resize())
})

watch(
    () => initData.weekMessages,
    () => chart?.setOption(buildOption()),
    { deep: true }
)
</script>

<template>
    <div ref="chartRef" class="today-chart"></div>
</template>

<style scoped>
.today-chart {
    width: 100%;
    height: 320px;
}
</style>