<script lang="ts" setup>
import {
    Warning,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth';
import * as echarts from 'echarts';
import { useInitData } from '@/stores/counter';

const init_data = useInitData()

type EChartsOption = echarts.EChartsOption
const chartRef = ref<HTMLDivElement>()
const authStore = useAuthStore()

onMounted(() => {
    if (chartRef.value) {
        const myChart = echarts.init(chartRef.value)
        const option: EChartsOption = {
            xAxis: {
                type: 'category',
                data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                axisLabel: {
                    fontSize: 12,
                    color: 'var(--text-regular)'
                }
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    fontSize: 12,
                    color: 'var(--text-regular)'
                }
            },
            series: [{
                data: [150, 230, 224, 218, 135, 147, 260],
                type: 'line',
                smooth: true,
                lineStyle: {
                    width: 3,
                    color: 'var(--chart-line)'
                },
                itemStyle: {
                    color: 'var(--chart-line)'
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'var(--chart-area-start)' },
                        { offset: 1, color: 'var(--chart-area-end)' }
                    ])
                }
            }],
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                top: '15%',
                containLabel: true
            },
            tooltip: {
                trigger: 'axis'
            }
        }
        myChart.setOption(option)
    }
})

const cards = [
    { value: init_data.message_count, title: '消息总数', tip: 'Total messages sent across all platforms', footer: '所有平台发送的消息总计' },
    { value: init_data.instance_count, title: '实例个数', tip: 'The number of Entari instances created', footer: '创建Entari实例的个数' },
    { value: init_data.runtime, title: '运行时间', tip: 'Entari Uptime', footer: 'Entari 运行时间' },
    { value: init_data.memory_usage, title: '内存占用', tip: 'Entari Memory Usage', footer: 'Entari 内存占用' },
]

const user_info = {
    username: authStore.user?.name ?? '未知用户',
    user_id: authStore.instances[0]?.id ?? '000000',
    role: '管理员',
    status: '正常',
    email: 'user@example.com',
    join_date: '2023-01-15',
    last_login: '2025-08-14 14:30:22'
}

</script>

<template>
    <div class="page">
        <div class="title">
            <h1 class="name">
                Entari Plugin WebUI
            </h1>
            <p>基于 Satori 协议的即时通信开发框架</p>
        </div>

        <div class="card">
            <el-row :gutter="16">
                <el-col :span="6" v-for="(item, idx) in cards" :key="idx" class="card_message">
                    <div class="statistic-card">
                        <el-statistic :value="item.value" :title="item.title">
                            <template #title>
                                <div style="display: inline-flex; align-items: center">
                                    {{ item.title }}
                                    <el-tooltip effect="dark" :content="item.tip" placement="top">
                                        <el-icon style="margin-left: 4px" :size="12">
                                            <Warning />
                                        </el-icon>
                                    </el-tooltip>
                                </div>
                            </template>
                        </el-statistic>

                        <div class="statistic-footer">
                            <div class="footer-item">
                                <span>{{ item.footer }}</span>
                            </div>
                        </div>
                    </div>
                </el-col>
            </el-row>
        </div>

        <div class="user-panel">
            <div class="panel-header">
                <h2>用户信息</h2>
            </div>

            <el-descriptions :column="4" class="user-info" direction="horizontal">
                <el-descriptions-item label="用户名" :span="2">
                    {{ user_info.username || '-' }}
                </el-descriptions-item>

                <el-descriptions-item label="用户 ID">
                    {{ user_info.user_id || '-' }}
                </el-descriptions-item>

                <el-descriptions-item label="角色">
                    <el-tag :type="user_info.role === '管理员' ? 'primary' : 'info'">
                        {{ user_info.role || '-' }}
                    </el-tag>
                </el-descriptions-item>

                <el-descriptions-item label="状态">
                    <el-tag :type="user_info.status === '正常' ? 'success' : 'danger'">
                        {{ user_info.status || '-' }}
                    </el-tag>
                </el-descriptions-item>

                <el-descriptions-item label="邮箱" :span="2">
                    {{ user_info.email || '-' }}
                </el-descriptions-item>

                <el-descriptions-item label="注册日期">
                    {{ user_info.join_date || '-' }}
                </el-descriptions-item>

                <el-descriptions-item label="最后登录" :span="4">
                    {{ user_info.last_login || '-' }}
                </el-descriptions-item>
            </el-descriptions>
        </div>

        <!-- 消息趋势图表 -->
        <div class="chart-panel">
            <div class="panel-header">
                <h2>本周消息趋势</h2>
            </div>
            <div ref="chartRef" class="chart"></div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.page {
    background-color: var(--main-bg);
    min-height: 100vh;
    border-radius: 30px;
    margin: 10px;
    padding-bottom: 40px;
    transition: background-color 0.3s, color 0.3s;
}

.title {
    margin-left: 40px;
    margin-top: 40px;

    .name {
        font-size: 80px;
        font-weight: bold;
        color: transparent;
        background-clip: text;
        -webkit-background-clip: text;
        background-image: linear-gradient(to right,
                var(--title-gradient-start),
                var(--title-gradient-end));
        background-size: 200% auto;
        animation: textGradient 2s linear infinite;

    }

    @keyframes textGradient {
        to {
            background-position: 200%;
        }
    }

    p {
        font-size: 50px;
        color: var(--title-text);
        margin-bottom: 30px;
    }
}

.card {
    padding: 20px;
}

.statistic-card {
    height: 100%;
    padding: 20px;
    border-radius: 6px;
    background-color: var(--card-bg);
    border: 1px solid var(--card-border);
    box-shadow: 0 2px 8px var(--card-shadow);
    transition: transform 0.3s ease, box-shadow 0.3s ease;

    &:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 16px var(--card-hover-shadow);
    }
}

:global(h2#card-usage ~ .example .example-showcase) {
    background-color: var(--el-fill-color) !important;
}

.el-statistic {
    --el-statistic-content-font-size: 28px;
}

.statistic-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    font-size: 15px;
    color: var(--text-regular);
    margin-top: 16px;
}

.statistic-footer .footer-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.statistic-footer .footer-item span:last-child {
    display: inline-flex;
    align-items: center;
    margin-left: 4px;
}

.user-panel,
.chart-panel {
    margin: 40px 20px 0;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px var(--card-shadow);
    border: 1px solid var(--card-border);
    overflow: hidden;
}

.panel-header {
    padding: 16px 20px;
    background: var(--panel-header-bg);
    border-bottom: 1px solid var(--el-border);

    h2 {
        font-size: 18px;
        font-weight: 600;
        color: var(--panel-header-text);
        margin: 0;
    }
}

.user-info {
    padding: 20px;

    :deep(.el-descriptions__label) {
        font-weight: 600;
        color: var(--text-primary);
    }

    :deep(.el-descriptions__content) {
        color: var(--text-primary);
    }
}

.chart {
    height: 400px;
    width: 100%;
    padding: 10px;
}

/* 移动端：单列显示 */
@media (max-width: 768px) {
    .user-info {
        --el-descriptions-column: 1;
    }

    .card .el-col {
        width: 100%;
        margin-bottom: 16px;
    }

    .title .name {
        font-size: 50px;
    }

    .title p {
        font-size: 30px;
    }
}
</style>