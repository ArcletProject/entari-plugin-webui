<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { listPlugins, togglePluginAPI } from '@/api/plugin'
import type { PluginItem } from '@/api/plugin'
import { ElMessage } from 'element-plus'
import ConfigDrawer from './PluginConfigForm.vue'

interface Plugin {
    name: string
    id: string
    title: string
    desc: string
    version: string
    author?: string
    status: boolean
    builtin?: boolean
    urls?: { homepage?: string }
    installed: boolean
}

const tableData = ref<Plugin[]>([])

onMounted(async () => {
    try {
        const raw = await listPlugins()
        tableData.value = raw.map(p => ({
            ...p,
            title: p.name,
            desc: p.desc || '暂无描述',
        }))
    } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        ElMessage.error('插件列表加载失败：' + msg)
    }
})

const pageSize = ref(10)
const currentPage = ref(1)
const keyword = ref('')
const viewMode = ref<'table' | 'card'>('table')
const cardPageSize = ref(6)
const cardCurrentPage = ref(1)

const configDrawerVisible = ref(false)
const currentPlugin = ref<PluginItem | null>(null)

function openConfigDrawer(plugin: PluginItem) {
    currentPlugin.value = plugin
    configDrawerVisible.value = true
}

const cardPagedData = computed(() =>
    filtered.value.slice(
        (cardCurrentPage.value - 1) * cardPageSize.value,
        cardCurrentPage.value * cardPageSize.value
    )
)

const filtered = computed(() =>
    tableData.value.filter(p =>
        p.title.includes(keyword.value) ||
        p.desc.includes(keyword.value) ||
        p.author?.includes(keyword.value)
    )
)

const pagedData = computed(() =>
    filtered.value.slice(
        (currentPage.value - 1) * pageSize.value,
        currentPage.value * pageSize.value
    )
)

function openDoc(name: string) {
    const plugin = tableData.value.find(p => p.name === name)
    const url = plugin?.urls?.homepage
    if (url) window.open(url.trim(), '_blank')
    else ElMessage.warning('暂无文档链接')
}

async function togglePlugin(plugin: PluginItem) {
    const next = !plugin.status
    await togglePluginAPI(plugin.id, !plugin.status)
    plugin.status = next
    ElMessage.success(next ? '已启用' : '已禁用')
}
</script>

<template>
    <div class="main-page">
        <div class="plugin-title">
            <div class="plugin-actions">
                <el-radio-group v-model="viewMode" size="large">
                    <el-radio-button label="table"><el-icon>
                            <IEpMenu />
                        </el-icon></el-radio-button>
                    <el-radio-button label="card"><el-icon>
                            <IEpGrid />
                        </el-icon></el-radio-button>
                </el-radio-group>

                <el-input v-model="keyword" placeholder="搜索插件" clearable />
            </div>

            <div v-if="viewMode === 'table'" class="plugin-message">
                <el-table :data="pagedData" style="width: 100%" stripe>
                    <el-table-column prop="title" label="名称" min-width="200" show-overflow-tooltip />
                    <el-table-column prop="desc" label="描述" min-width="300" show-overflow-tooltip />
                    <el-table-column prop="version" label="版本" width="100" show-overflow-tooltip />
                    <el-table-column prop="author" label="作者" width="120" show-overflow-tooltip />
                    <el-table-column label="状态" width="80">
                        <template #default="{ row }">
                            <el-switch :model-value="row.status" @change="togglePlugin(row)" />
                        </template>
                    </el-table-column>
                    <el-table-column label="操作" width="260">
                        <template #default="{ row }">
                            <el-button-group>
                                <template v-if="row.builtin">
                                    <el-button size="small" type="warning">更新</el-button>
                                    <el-button size="small" type="primary" @click="openDoc(row.name)">查看文档</el-button>
                                    <el-button size="small" type="primary" @click="openConfigDrawer(row)">配置</el-button>
                                </template>

                                <template v-else>
                                    <el-button size="small">
                                        {{ row.status ? '禁用' : '启用' }}
                                    </el-button>
                                    <el-button size="small" type="warning">更新</el-button>
                                    <el-button size="small" type="primary" @click="openDoc(row.name)">查看文档</el-button>
                                    <el-button size="small" type="primary" @click="openConfigDrawer(row)">配置</el-button>
                                    <el-button size="small" type="danger">卸载</el-button>
                                </template>
                            </el-button-group>
                        </template>
                    </el-table-column>
                </el-table>

                <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="filtered.length"
                    layout="total, sizes, prev, pager, next, jumper"
                    style="margin-top: 16px; justify-content: flex-end" />
                <ConfigDrawer v-model="configDrawerVisible" :plugin="currentPlugin!" @closed="currentPlugin = null" />
            </div>

            <div v-else class="card-view">
                <el-row :gutter="20">
                    <el-col v-for="plugin in cardPagedData" :key="plugin.name" :xs="24" :sm="12" :md="8">
                        <el-card shadow="hover" class="plugin-card">
                            <template #header>
                                <div class="card-header">
                                    <el-tooltip :content="plugin.title" placement="top">
                                        <strong>{{ plugin.title }}</strong>
                                    </el-tooltip>
                                    <el-tag size="small" :type="plugin.status ? 'success' : 'info'">
                                        {{ plugin.status ? '启用' : '禁用' }}
                                    </el-tag>
                                </div>
                            </template>

                            <el-tooltip :content="plugin.desc" placement="top">
                                <p class="desc ellipsis-2">{{ plugin.desc }}</p>
                            </el-tooltip>

                            <div class="meta">
                                <el-tooltip :content="`作者：${plugin.author}`" placement="top">
                                    <span class="ellipsis">作者：{{ plugin.author }}</span>
                                </el-tooltip>
                                <span>版本：{{ plugin.version }}</span>
                            </div>

                            <template #footer>
                                <div class="footer-btns">
                                    <template v-if="plugin.builtin">
                                        <el-button size="small" type="primary" text
                                            @click="openDoc(plugin.name)">查看文档</el-button>
                                        <el-button size="small" type="primary" text
                                            @click="openConfigDrawer(plugin)">配置</el-button>
                                        <el-button size="small" type="warning" text>更新</el-button>
                                    </template>

                                    <template v-else>
                                        <el-switch :model-value="plugin.status" @change="togglePlugin(plugin)"
                                            style="margin-right: 8px" />
                                        <el-button size="small" text>{{ plugin.status ? '禁用' : '启用' }}</el-button>
                                        <el-button size="small" type="warning" text>更新</el-button>
                                        <el-button size="small" type="primary" text
                                            @click="openDoc(plugin.name)">查看文档</el-button>
                                        <el-button size="small" type="primary" text
                                            @click="openConfigDrawer(plugin)">配置</el-button>
                                        <el-button size="small" type="danger" text>卸载</el-button>
                                    </template>
                                </div>
                            </template>
                        </el-card>
                    </el-col>
                </el-row>

                <el-pagination v-model:current-page="cardCurrentPage" :page-size="cardPageSize" :total="filtered.length"
                    layout="total, prev, pager, next, jumper" style="margin-top: 16px; justify-content: flex-end" />

                <ConfigDrawer v-model="configDrawerVisible" :plugin="currentPlugin!" @closed="currentPlugin = null" />
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.main-page {
    background: var(--plugin-page-bg);
    margin: 30px;
    border-radius: 5px;
    height: 88vh;
    box-shadow: 0 4px 12px var(--plugin-card-shadow);
}

.plugin-title {
    padding: 20px;
    flex-wrap: wrap;
}

.plugin-header {
    display: flex;
    align-items: center;
    gap: 15px;

    img {
        width: 50px;
        height: 50px;
        border-radius: 4px;
    }

    .t1 {
        font-weight: bold;
    }

    .t2 {
        color: #A3A3A3;
        font-size: 14px;
    }
}

.plugin-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-shrink: 0;
    margin-top: 20px;

    .el-radio-group {
        display: flex;
        flex-direction: row;
    }

    .el-input {
        width: 500px;
        background: var(--plugin-input-bg);
        border: 1px solid var(--plugin-input-border);
    }
}

.plugin-message {
    margin-top: 20px;
    width: auto;
}

.el-row {
    border-radius: 5px;
}

.plugin-card {
    margin-top: 20px;
    background: var(--plugin-card-bg);
    border: 1px solid var(--plugin-card-border);
    box-shadow: 0 2px 8px var(--plugin-card-shadow);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--plugin-header-text);
    transition: color 0.3s;
}

.desc {
    font-size: 14px;
    color: var(--plugin-desc-text);
    margin: 8px 0;
    transition: color 0.3s;
}

.meta {
    font-size: 13px;
    color: var(--plugin-meta-text);
    display: flex;
    flex-direction: column;
    gap: 4px;
    transition: color 0.3s;
}

.footer-btns {
    display: flex;
    gap: 8px;
}

.plugin-message .el-button-group .el-button+.el-button {
    margin-left: 2px;
}

:deep(.el-table) {
    background: var(--plugin-card-bg);
    color: var(--plugin-header-text);
}

:deep(.el-table th),
:deep(.el-table td) {
    border-bottom: 1px solid var(--plugin-panel-border);
}

:deep(.el-table th) {
    background: var(--plugin-panel-bg);
    color: var(--plugin-header-text);
}

:deep(.el-table tr:hover) {
    background: var(--plugin-panel-bg);
}

.ellipsis {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* 两行省略 */
.ellipsis-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;

    line-clamp: 2;
    box-orient: vertical;
}
</style>