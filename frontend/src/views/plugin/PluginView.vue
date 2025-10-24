<script lang="ts" setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import { ElMessage, ElDialog, ElDescriptions, ElDescriptionsItem } from 'element-plus'
import { listPlugins, togglePluginAPI } from '@/api/plugin'
import type { PluginItem, RawAuthor } from '@/api/plugin'
import ConfigDrawer from './PluginConfigForm.vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({ async: false })
type AuthorItem = { name?: string; email?: string } | string

interface PluginInfo {
    name: string
    version: string
    author: string
    license: string
    description: string
    homepage: string
    depend_services: string[]
    readme?: string
}

function parseAuthor(raw?: RawAuthor): string {
    if (!raw) return '-'
    if (typeof raw === 'string') return raw.trim() || '-'
    if (Array.isArray(raw))
        return raw
            .map((i: AuthorItem) =>
                typeof i === 'string' ? i : `${i.name || ''} <${i.email || ''}>`.trim()
            )
            .join(' , ')
    return `${raw.name || ''} <${raw.email || ''}>`.trim() || '-'
}

function normalizeMeta(p: PluginItem): PluginInfo {
    const m = p.meta === null || p.meta === 'None' ? undefined : p.meta
    if (m && typeof m === 'object') {
        return {
            name: m.name ?? p.name,
            version: m.version ?? p.version ?? '-',
            author: parseAuthor(m.author ?? m.authors),
            license: m.license ?? '-',
            description: m.description ?? p.desc ?? '-',
            homepage: m.urls?.homepage ?? p.urls?.homepage ?? '',
            depend_services: Array.isArray(m.depend_services) ? m.depend_services : [],
            readme: m.readme ?? ''
        }
    }
    return {
        name: p.name,
        version: p.version ?? '-',
        author: parseAuthor(p.author),
        license: '-',
        description: p.desc ?? '-',
        homepage: p.urls?.homepage ?? '',
        depend_services: [],
        readme: p.readme ?? '-',
    }
}

const PluginDetailDialog = defineComponent({
    name: 'PluginDetailDialog',
    props: {
        visible: { type: Boolean, default: false },
        info: { type: Object, default: () => ({}) }
    },
    emits: ['update:visible'],
    setup(props, { emit }) {
        const show = computed({ get: () => props.visible, set: v => emit('update:visible', v) })
        return () =>
            h(
                ElDialog,
                {
                    modelValue: show.value,
                    'onUpdate:modelValue': (v: boolean) => (show.value = v),
                    title: '插件详情',
                    width: 800
                },
                () =>
                    h(ElDescriptions, { column: 1, border: true }, () => [
                        h(ElDescriptionsItem, { label: '名称' }, () => props.info.name),
                        h(ElDescriptionsItem, { label: '版本' }, () => props.info.version),
                        h(ElDescriptionsItem, { label: '作者' }, () => props.info.author),
                        h(ElDescriptionsItem, { label: '许可证' }, () => props.info.license),
                        h(ElDescriptionsItem, { label: '描述' }, () => props.info.description),
                        h(ElDescriptionsItem, { label: '详细内容', span: 2 }, () =>
                            props.info.readme
                                ? h('div', {
                                    class: 'readme-box',
                                    innerHTML: DOMPurify.sanitize(marked.parse(props.info.readme as string) as string)
                                })
                                : '-'
                        ),
                        h(ElDescriptionsItem, { label: '依赖服务' }, () =>
                            props.info.depend_services.length
                                ? props.info.depend_services.join(' , ')
                                : '-'
                        )
                    ])
            )
    }
})

const tableData = ref<PluginItem[]>([])

onMounted(async () => {
    try {
        const raw = await listPlugins()
        tableData.value = raw.map(p => ({
            ...p,
            title: p.name,
            desc: p.desc || '暂无描述',
            meta: p.meta
        }))
    } catch (e: unknown) {
        ElMessage.error('插件列表加载失败：' + (e instanceof Error ? e.message : String(e)))
    }
})

const pageSize = ref(10)
const currentPage = ref(1)
const keyword = ref('')
const viewMode = ref<'table' | 'card'>('table')
const cardPageSize = ref(6)
const cardCurrentPage = ref(1)

const filtered = computed(() =>
    tableData.value.filter(p =>
        [p.title, p.desc, p.author].some(s => s?.includes(keyword.value))
    )
)

const pagedData = computed(() =>
    filtered.value.slice(
        (currentPage.value - 1) * pageSize.value,
        currentPage.value * pageSize.value
    )
)

const cardPagedData = computed(() =>
    filtered.value.slice(
        (cardCurrentPage.value - 1) * cardPageSize.value,
        cardCurrentPage.value * cardPageSize.value
    )
)

const configDrawerVisible = ref(false)
const currentPlugin = ref<PluginItem | null>(null)

function openConfigDrawer(plugin: PluginItem) {
    currentPlugin.value = plugin
    configDrawerVisible.value = true
}

const detailVisible = ref(false)
const currentInfo = ref<PluginInfo>({} as PluginInfo)

function openDoc(plugin: PluginItem) {
    currentInfo.value = normalizeMeta(plugin)
    detailVisible.value = true
}

async function togglePlugin(plugin: PluginItem) {
    const next = !plugin.status
    await togglePluginAPI(plugin.id, next)
    plugin.status = next
    ElMessage.success(next ? '已启用' : '已禁用')
}
</script>

<template>
    <div class="main-page">
        <div class="plugin-title">
            <div class="plugin-actions">
                <el-radio-group v-model="viewMode" size="large">
                    <el-radio-button label="table">
                        <el-icon>
                            <IEpMenu />
                        </el-icon>
                    </el-radio-button>
                    <el-radio-button label="card">
                        <el-icon>
                            <IEpGrid />
                        </el-icon>
                    </el-radio-button>
                </el-radio-group>
                <el-input v-model="keyword" placeholder="搜索插件" clearable />
            </div>

            <!-- 表格模式 -->
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
                                    <el-button size="small" type="primary" @click="openDoc(row)">详情</el-button>
                                    <el-button size="small" type="primary" @click="openConfigDrawer(row)">配置</el-button>
                                </template>
                                <template v-else>
                                    <el-button size="small">{{ row.status ? '禁用' : '启用' }}</el-button>
                                    <el-button size="small" type="warning">更新</el-button>
                                    <el-button size="small" type="primary" @click="openDoc(row)">详情</el-button>
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
            </div>

            <!-- 卡片模式 -->
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
                                            @click="openDoc(plugin)">详情</el-button>
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
                                            @click="openDoc(plugin)">详情</el-button>
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
            </div>
        </div>

        <PluginDetailDialog v-model:visible="detailVisible" :info="currentInfo" />
        <ConfigDrawer v-model="configDrawerVisible" :plugin="currentPlugin!" @closed="currentPlugin = null" />
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
        color: #a3a3a3;
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

.ellipsis-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-clamp: 2;
    box-orient: vertical;
}

:deep(.readme-box) {
    max-height: 230px;
    overflow: auto;
    padding: 30px;
    background: var(--el-bg-color);
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
    line-height: 1.6;
}

:deep(.readme-box blockquote) {
    margin: 0;
    padding: 0 1em;
    color: var(--el-text-color-secondary);
    border-left: 0.25em solid var(--el-border-color);
}

:deep(.readme-box pre) {
    background: var(--el-fill-color-lighter);
    padding: 8px;
    overflow: auto;
    border-radius: 4px;
}

:deep(.readme-box code) {
    background: var(--el-fill-color-lighter);
    padding: 2px 4px;
    border-radius: 3px;
}

:deep(.readme-box img) {
    max-width: 100%;
}
</style>
