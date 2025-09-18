<script setup lang="ts">
import { ref, computed } from 'vue'
import { installPlugin, uninstallPlugin, listMarketPlugins } from '@/api/plugin'
import type { MarketItem } from '@/api/plugin'
import { ElMessage } from 'element-plus'

interface Plugin {
    name: string
    fullName: string
    desc: string
    author?: string
    stars: number
    updated: string
    tags: string[]
    installed: boolean
}

const allPlugins = ref<MarketItem[]>([])

const keyword = ref('')
const filterTag = ref('')
const tagOptions = ['全部', '推荐', '媒体', '统计', '游戏', '工具', '实用']

const filteredPlugins = computed(() => {
    return allPlugins.value.filter(p =>
        p.name.toLowerCase().includes(keyword.value.toLowerCase()) &&
        (filterTag.value === '全部' || filterTag.value === '' || p.tags.includes(filterTag.value))
    )
})

const pageSize = ref(6)
const currentPage = ref(1)
const pagedPlugins = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    return filteredPlugins.value.slice(start, start + pageSize.value)
})

const installing = ref<Set<string>>(new Set())

const handleInstall = async (p: Plugin) => {
    installing.value.add(p.name)
    try {
        await installPlugin(p.name)
        p.installed = true
        ElMessage.success('安装成功')
    } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        ElMessage.error(msg || '安装失败')
    } finally {
        installing.value.delete(p.name)
    }
}

const handleUninstall = async (p: Plugin) => {
    installing.value.add(p.name);
    try {
        await uninstallPlugin(p.name);
        p.installed = false;
        ElMessage.success('卸载成功');
    } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        ElMessage.error(msg || '卸载失败');
    } finally {
        installing.value.delete(p.name);
    }
}

onMounted(async () => {
    const response = await listMarketPlugins();
    allPlugins.value = response
});
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
                    <div class="tags">
                        <el-tag v-for="tag in p.tags" :key="tag">{{ tag }}</el-tag>
                    </div>
                    <div class="actions">
                        <el-button size="small" text>查看文档</el-button>
                        <el-button size="small" :type="p.installed ? 'danger' : 'primary'"
                            :disabled="installing.has(p.name)" :loading="installing.has(p.name)"
                            @click="p.installed ? handleUninstall(p) : handleInstall(p)">
                            {{ p.installed ? '卸载' : '安装' }}
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