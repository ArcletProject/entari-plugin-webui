<script setup lang="ts">
import { ref, computed } from 'vue'

/* 1. 模拟接口返回的插件列表 */
interface Plugin {
    name: string
    fullName: string
    desc: string
    author: string
    stars: number
    updated: string
    tags: string[]
    installed: boolean
}
const allPlugins = ref<Plugin[]>([
    {
        name: 'astrbot_plugin_bilibili',
        fullName: '哔哩哔哩动态推送',
        desc: '哔哩哔哩动态推送、视频信息、直播间信息查询插件',
        author: 'Flartiny & Soulter',
        stars: 49,
        updated: '2025/7/14 20:25',
        tags: ['推荐', '媒体'],
        installed: true
    },
    {
        name: 'astrbot_plugin_cloudrank',
        fullName: 'AstrBot词云与排名插件',
        desc: '支持群聊与私聊消息，生成美观词云图，并展示用户活跃度排行。',
        author: 'GEMILUXVII',
        stars: 9,
        updated: '2025/7/12 16:12',
        tags: ['统计', '可视化'],
        installed: false
    },
    {
        name: 'pet',
        fullName: '内宠物养成插件',
        desc: '一个简单的内宠物养成插件，支持LLM随机事件、PVP对决和图片状态卡。',
        author: 'DITF16',
        stars: 0,
        updated: '2025/7/14 20:25',
        tags: ['游戏', '趣味'],
        installed: false
    },
    {
        name: 'error_monitor',
        fullName: 'ImmersiveError 捕获器',
        desc: '捕获 ImmersiveError 抛出的异常，并通过 SMTP 邮件通知。',
        author: 'Magstic',
        stars: 0,
        updated: '2025/7/12 16:12',
        tags: ['工具', '实用'],
        installed: false
    }
])

/* 2. 搜索 & 过滤 */
const keyword = ref('')
const filterTag = ref('')
const tagOptions = ['全部', '推荐', '媒体', '统计', '游戏', '工具', '实用']

const filteredPlugins = computed(() => {
    return allPlugins.value.filter(p =>
        p.name.toLowerCase().includes(keyword.value.toLowerCase()) &&
        (filterTag.value === '全部' || filterTag.value === '' || p.tags.includes(filterTag.value))
    )
})

/* 3. 分页 */
const pageSize = ref(6)
const currentPage = ref(1)
const pagedPlugins = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    return filteredPlugins.value.slice(start, start + pageSize.value)
})
</script>

<template>
    <div class="plugin-market">
        <!-- 顶部搜索 & 标签 -->
        <div class="header">
            <el-input v-model="keyword" placeholder="Search" prefix-icon="Search" style="width: 260px" />
            <el-select v-model="filterTag" placeholder="标签" style="width: 120px; margin-left: 12px">
                <el-option v-for="t in tagOptions" :key="t" :label="t" :value="t" />
            </el-select>
        </div>

        <!-- 插件卡片列表 -->
        <el-row :gutter="20" class="list">
            <el-col v-for="p in pagedPlugins" :key="p.name" :xs="24" :sm="12" :md="8" style="margin-bottom: 20px">
                <el-card shadow="hover" class="plugin-card">
                    <!-- 顶部标题 -->
                    <div class="title">
                        <span>{{ p.fullName }}</span>
                        <el-tag v-if="p.installed" size="small" type="success">已安装</el-tag>
                    </div>
                    <!-- 描述 -->
                    <p class="desc">{{ p.desc }}</p>
                    <!-- 作者 & star -->
                    <div class="meta">
                        <span>@{{ p.author }}</span>
                        <span><el-icon>
                                <StarFilled />
                            </el-icon>{{ p.stars }}</span>
                    </div>
                    <!-- 标签 -->
                    <div class="tags">
                        <el-tag v-for="tag in p.tags" :key="tag">{{ tag }}</el-tag>
                    </div>
                    <!-- 操作 -->
                    <div class="actions">
                        <el-button size="small" text>查看文档</el-button>
                        <el-button size="small" :type="p.installed ? 'info' : 'primary'" :disabled="p.installed">
                            {{ p.installed ? '已安装' : '安装' }}
                        </el-button>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 分页 -->
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="filteredPlugins.length"
            layout="prev, pager, next" style="justify-content: center; margin-top: 20px" />
    </div>
</template>

<style scoped>
.plugin-market {
    padding: 24px;
    background: var(--market-bg);
    min-height: 100vh;
}

.header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}

.plugin-card {
    border-radius: 12px;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--market-card-bg);
    border: 1px solid var(--market-card-border);
    box-shadow: 0 2px 12px var(--market-card-shadow);
}

.title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
    font-weight: 600;
    color: var(--market-header-text);
    transition: color 0.3s;
}

.desc {
    margin: 8px 0;
    font-size: 14px;
    color: var(--market-desc-text);
    flex: 1;
    transition: color 0.3s;
}

.meta {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    color: var(--market-meta-text);
    margin-bottom: 8px;
    transition: color 0.3s;
}

.tags {
    margin-bottom: 12px;
}

.tags .el-tag {
    margin-right: 6px;
    background: var(--market-tag-bg);
    color: var(--market-tag-text);
    border: none;
}

.actions {
    display: flex;
    justify-content: space-between;
}

:deep(.el-button--primary) {
    background: var(--market-btn-primary-bg);
    border-color: var(--market-btn-primary-bg);
    color: var(--market-btn-primary-text);
}

:deep(.el-button--info) {
    background: var(--market-btn-info-bg);
    border-color: var(--market-btn-info-bg);
    color: var(--market-btn-info-text);
}

:deep(.el-input__inner),
:deep(.el-select .el-input__inner) {
    background: var(--market-input-bg);
    border-color: var(--market-input-border);
    color: var(--market-input-text);
}

:deep(.el-input__inner::placeholder) {
    color: var(--market-meta-text);
}

:deep(.el-pagination) {
    background: var(--market-pagination-bg);
    color: var(--market-pagination-text);
}

:deep(.el-pager li) {
    background: var(--market-pagination-bg);
    color: var(--market-pagination-text);
}

:deep(.el-pager li.active) {
    background: var(--market-btn-primary-bg);
    color: var(--market-btn-primary-text);
}
</style>