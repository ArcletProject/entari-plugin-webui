<script lang="ts" setup>
import { ref, computed } from 'vue'

interface Plugin {
    name: string
    title: string
    desc: string
    version: string
    author: string
    status: boolean
    builtin?: boolean
}

interface Document {
    name: string
    url: string
}

const tableData = ref<Plugin[]>([
    {
        name: 'entari-plugin-server',
        title: 'entari-plugin-server',
        desc: '为 Entari 提供 Satori 服务器支持，基于此为 Entari 提供 ASGI 服务、适配器连接等功能',
        version: '0.2.3',
        author: 'RF-Tar-Railt',
        status: true,
        builtin: true
    },
    {
        name: 'entari-plugin-database',
        title: 'entari-plugin-database',
        desc: '为 Entari 提供统一的数据库抽象层，支持 SQLite 等多种后端，实现插件数据持久化与迁移管理。',
        version: '0.1.1',
        author: 'RF-Tar-Railt',
        status: true,
        builtin: true
    }
])

const document_url = ref<Document[]>([
    {
        name: 'entari-plugin-server',
        url: 'https://arclet.top/tutorial/entari/server.html'
    },
    {
        name: 'entari-plugin-database',
        url: 'https://arclet.top/tutorial/entari/database.html'
    }
])

const pageSize = ref(10)
const currentPage = ref(1)
const keyword = ref('')
const viewMode = ref<'table' | 'card'>('table')

const filtered = computed(() =>
    tableData.value.filter(p =>
        p.title.includes(keyword.value) ||
        p.desc.includes(keyword.value) ||
        p.author.includes(keyword.value)
    )
)

const pagedData = computed(() =>
    filtered.value.slice(
        (currentPage.value - 1) * pageSize.value,
        currentPage.value * pageSize.value
    )
)

function openDoc(name: string) {
    const doc = document_url.value.find(d => d.name === name)
    if (doc) {
        window.open(doc.url.trim(), '_blank')
    } else {
        ElMessage.warning('暂无文档链接')
    }
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
                    <el-table-column prop="title" label="名称" min-width="200" />
                    <el-table-column prop="desc" label="描述" min-width="300" />
                    <el-table-column prop="version" label="版本" width="100" />
                    <el-table-column prop="author" label="作者" width="120" />
                    <el-table-column prop="status" label="状态" width="80">
                        <template #default="{ row }">
                            <el-tag :type="row.status ? 'success' : 'info'">
                                {{ row.status ? '启用' : '禁用' }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作" width="260">
                        <template #default="{ row }">
                            <el-button-group>
                                <template v-if="row.builtin">
                                    <el-button size="small" type="warning">更新</el-button>
                                    <el-button size="small" type="primary" @click="openDoc(row.name)">查看文档</el-button>
                                </template>

                                <template v-else>
                                    <el-button size="small">
                                        {{ row.status ? '禁用' : '启用' }}
                                    </el-button>
                                    <el-button size="small" type="warning">更新</el-button>
                                    <el-button size="small" type="primary" @click="openDoc(row.name)">查看文档</el-button>
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

            <div v-else class="card-view">
                <el-row :gutter="20">
                    <el-col v-for="plugin in filtered" :key="plugin.name" :xs="24" :sm="12" :md="8">
                        <el-card shadow="hover" class="plugin-card">
                            <template #header>
                                <div class="card-header">
                                    <strong>{{ plugin.title }}</strong>
                                    <el-tag size="small" :type="plugin.status ? 'success' : 'info'">
                                        {{ plugin.status ? '启用' : '禁用' }}
                                    </el-tag>
                                </div>
                            </template>

                            <p class="desc">{{ plugin.desc }}</p>
                            <div class="meta">
                                <span>作者：{{ plugin.author }}</span>
                                <span>版本：{{ plugin.version }}</span>
                            </div>

                            <template #footer>
                                <div class="footer-btns">
                                    <template v-if="plugin.builtin">
                                        <el-button size="small" type="primary" text
                                            @click="openDoc(plugin.name)">查看文档</el-button>
                                        <el-button size="small" type="warning" text>更新</el-button>
                                    </template>

                                    <template v-else>
                                        <el-button size="small" text>
                                            {{ plugin.status ? '禁用' : '启用' }}
                                        </el-button>
                                        <el-button size="small" type="warning" text>更新</el-button>
                                        <el-button size="small" type="primary" text
                                            @click="openDoc(plugin.name)">查看文档</el-button>
                                        <el-button size="small" type="danger" text>卸载</el-button>
                                    </template>
                                </div>
                            </template>
                        </el-card>
                    </el-col>
                </el-row>
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
    transition: background 0.3s, box-shadow 0.3s;
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
        transition: background 0.3s, border-color 0.3s;
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
    transition: background 0.3s, border-color 0.3s, box-shadow 0.3s;
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
    transition: background 0.3s, color 0.3s;
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
</style>