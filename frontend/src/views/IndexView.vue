<script setup lang="ts">
import { computed } from 'vue'
import { onMounted } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useInitData } from '@/stores/counter'
import TodayChart from '@/views/component/TodayChart.vue'

const authStore = useAuthStore()
const initData = useInitData()

onMounted(async () => {
    await initData.fetchInitData()
})

const pluginRate = computed(() => {
    const total = initData.plugin_total || 1
    const enabled = initData.plugin_enabled || 0
    return Math.round((enabled / total) * 100)
})

const runtimeMinutes = computed(() => initData.runtime || 0)

const cards = computed(() => [
    {
        value: initData.message_count,
        title: '消息总数',
        tip: 'All platforms total messages',
        footer: '所有平台累计接收',
        unit: '条'
    },
    {
        value: initData.today_messages ?? 0,
        title: '今日消息量',
        tip: 'Messages received today',
        footer: '本自然日 00:00 起',
        unit: '条'
    },
    {
        value: pluginRate.value,                      // ✅ 响应式
        title: '插件启用率',
        tip: 'Enabled plugin ratio',
        footer: `已启用 ${initData.plugin_enabled ?? 0} / 总计 ${initData.plugin_total ?? 0}`,
        unit: '%'
    },
    {
        value: runtimeMinutes.value,                  // ✅ 响应式
        title: '运行时长',
        tip: 'Entari continuous uptime',
        footer: '自启动以来连续运行',
        unit: '分'
    }
])

/*---------- 用户信息 ----------*/
const userInfo = {
    username: authStore.user?.name ?? '未知用户',
    user_id: authStore.instances[0]?.id ?? '000000',
    role: '管理员',
    status: '正常',
    email: 'user@example.com',
    last_login: '2025-08-14 14:30:22'
}
</script>

<template>
    <div class="page">
        <div class="title">
            <h1 class="name">Entari Plugin WebUI</h1>
            <p>基于 Satori 协议的即时通信开发框架</p>
        </div>

        <!-- 四张指标卡片 -->
        <div class="card">
            <el-row :gutter="16">
                <el-col :xs="24" :sm="12" :md="6" v-for="(item, idx) in cards" :key="idx" class="card_message">
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
                            <template #suffix>{{ item.unit }}</template>
                        </el-statistic>
                        <div class="statistic-footer">{{ item.footer }}</div>
                    </div>
                </el-col>
            </el-row>
        </div>

        <!-- 用户信息 -->
        <div class="user-panel">
            <div class="panel-header">
                <h2>用户信息</h2>
            </div>
            <el-descriptions :column="4" direction="horizontal" class="user-info">
                <el-descriptions-item label="用户名" :span="2">
                    {{ userInfo.username }}
                </el-descriptions-item>
                <el-descriptions-item label="用户 ID">
                    {{ userInfo.user_id }}
                </el-descriptions-item>
                <el-descriptions-item label="角色">
                    <el-tag :type="userInfo.role === '管理员' ? 'primary' : 'info'">
                        {{ userInfo.role }}
                    </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="状态">
                    <el-tag :type="userInfo.status === '正常' ? 'success' : 'danger'">
                        {{ userInfo.status }}
                    </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="邮箱" :span="2">
                    {{ userInfo.email }}
                </el-descriptions-item>
                <el-descriptions-item label="最后登录" :span="4">
                    {{ userInfo.last_login }}
                </el-descriptions-item>
            </el-descriptions>
        </div>

        <div class="card">
            <TodayChart />
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

.statistic-footer {
    margin-top: 12px;
    font-size: 14px;
    color: var(--text-regular);
}

.user-panel {
    margin: 40px 20px 0;
    background: var(--card-bg);
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

@media (max-width: 768px) {
    .title .name {
        font-size: 50px;
    }

    .title p {
        font-size: 30px;
    }

    .card .el-col {
        width: 100%;
        margin-bottom: 16px;
    }
}
</style>