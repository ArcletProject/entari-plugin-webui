<script setup lang="ts">
import { ref, computed, defineComponent, h } from 'vue'
import { installPlugin, uninstallPlugin, listMarketPlugins } from '@/api/plugin'
import type { MarketItem, RawAuthor } from '@/api/plugin'
import { ElMessage, ElDialog, ElDescriptions, ElDescriptionsItem } from 'element-plus'
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
function normalizeMeta(p: MarketItem): PluginInfo {
    const m = p.meta == null || p.meta === 'None' ? undefined : p.meta
    if (m && typeof m === 'object') {
        return {
            name: m.name ?? p.name,
            version: m.version ?? p.version ?? '-',
            author: parseAuthor(m.author ?? m.authors),
            license: m.license ?? '-',
            description: m.description ?? p.desc ?? '-',
            homepage: p?.homepage ?? '',
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
        homepage: p?.homepage ?? '',
        depend_services: [],
        readme: ''
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
                                    innerHTML: DOMPurify.sanitize(marked.parse(props.info.readme) as string)
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
/* -------------------------------------------------- */

const allPlugins = ref<MarketItem[]>([])
const keyword = ref('')
const filterTag = ref('')
const tagOptions = ['全部', '推荐', '媒体', '统计', '游戏', '工具', '实用']

const filteredPlugins = computed(() =>
    allPlugins.value.filter(
        p =>
            p.name.toLowerCase().includes(keyword.value.toLowerCase()) &&
            (filterTag.value === '全部' || filterTag.value === '' || p.tags.includes(filterTag.value))
    )
)

const pageSize = ref(6)
const currentPage = ref(1)
const pagedPlugins = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    return filteredPlugins.value.slice(start, start + pageSize.value)
})

const installing = ref<Set<string>>(new Set())

/* -------- 2. 弹窗相关响应式 & 方法 -------- */
const detailVisible = ref(false)
const currentInfo = ref<PluginInfo>({} as PluginInfo)
function openDoc(p: MarketItem) {
    currentInfo.value = normalizeMeta(p)
    detailVisible.value = true
}
/* ----------------------------------------- */

async function handleInstall(p: MarketItem) {
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

async function handleUninstall(p: MarketItem) {
    installing.value.add(p.name)
    try {
        await uninstallPlugin(p.name)
        p.installed = false
        ElMessage.success('卸载成功')
    } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        ElMessage.error(msg || '卸载失败')
    } finally {
        installing.value.delete(p.name)
    }
}

function onCardClick(e: MouseEvent, p: MarketItem) {
    const target = e.target as HTMLElement
    if (target.closest('.el-button, .el-tag')) return

    if (p.homepage) {
        window.open(p.homepage, '_blank', 'noopener')
    }
}

onMounted(async () => {
    allPlugins.value = await listMarketPlugins()
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

        <el-row :gutter="20" class="list">
            <el-col v-for="p in pagedPlugins" :key="p.name" :xs="24" :sm="12" :md="8" style="margin-bottom: 20px">
                <!-- 整卡点击 -->
                <el-card shadow="hover" class="plugin-card" @click="onCardClick($event, p)">
                    <template #header>
                        <div class="card-header">
                            <span class="title-text">{{ p.fullName }}</span>
                            <el-tag v-if="p.installed" size="small" type="success">已安装</el-tag>
                            <!-- 详情按钮 -->
                            <el-button size="small" text @click.stop="openDoc(p)">详情</el-button>
                        </div>
                    </template>

                    <p class="desc">{{ p.desc }}</p>

                    <div class="tags">
                        <el-tag v-for="tag in p.tags" :key="tag">{{ tag }}</el-tag>
                    </div>

                    <div class="bottom-info">
                        <span>@{{ p.author }}</span>
                        <span>v{{ p.version }}</span>
                    </div>

                    <div class="actions">
                        <!-- 安装/卸载按钮 -->
                        <el-button size="small" :type="p.installed ? 'danger' : 'primary'"
                            :disabled="installing.has(p.name)" :loading="installing.has(p.name)"
                            @click.stop="p.installed ? handleUninstall(p) : handleInstall(p)">
                            {{ p.installed ? '卸载' : '安装' }}
                        </el-button>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="filteredPlugins.length"
            layout="prev, pager, next" style="justify-content: center; margin-top: 20px" />

        <!-- 弹窗 -->
        <PluginDetailDialog v-model:visible="detailVisible" :info="currentInfo" />
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
    align-items: center;
    justify-content: flex-start;
    height: 50px;
    border-top: 1px solid #aeaeae;
    margin-top: 12px;
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

.card-header {
    display: flex;
    align-items: center;
    gap: 6px;
}

.card-header .title-text {
    font-weight: 600;
    font-size: 16px;
    color: var(--market-header-text);
    transition: color 0.3s;
}

.card-header .el-button {
    margin-left: auto;
}

.bottom-info {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    color: var(--market-meta-text);
    margin-top: 8px;
}

.card-link {
    display: block;
    text-decoration: none;
    color: inherit;
}
</style>