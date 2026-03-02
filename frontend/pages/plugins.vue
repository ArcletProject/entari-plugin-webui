<template>
  <div class="plugins-page">
    <n-card title="插件管理">
      <template #header-extra>
        <n-input
          v-model:value="searchText"
          placeholder="搜索插件"
          clearable
          style="width: 200px"
        >
          <template #prefix>
            <Icon name="mdi:magnify" />
          </template>
        </n-input>
      </template>

      <n-data-table
        :columns="columns"
        :data="filteredPlugins"
        :loading="loading"
        :pagination="pagination"
      />
    </n-card>

    <!-- 配置编辑抽屉 -->
    <n-drawer v-model:show="showConfigDrawer" width="500">
      <n-drawer-content :title="`配置 - ${currentPlugin?.name}`">
        <n-form v-if="currentPlugin" :model="configForm">
          <n-form-item
            v-for="(value, key) in currentPlugin.config"
            :key="key"
            :label="String(key)"
          >
            <template v-if="typeof value === 'boolean'">
              <n-switch v-model:value="configForm[key]" />
            </template>
            <template v-else-if="typeof value === 'number'">
              <n-input-number v-model:value="configForm[key]" />
            </template>
            <template v-else-if="Array.isArray(value)">
              <n-dynamic-input v-model:value="configForm[key]" />
            </template>
            <template v-else>
              <n-input v-model:value="configForm[key]" />
            </template>
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space>
            <n-button @click="showConfigDrawer = false">取消</n-button>
            <n-button type="primary" :loading="saving" @click="saveConfig">
              保存
            </n-button>
          </n-space>
        </template>
      </n-drawer-content>
    </n-drawer>

    <!-- 插件详情 -->
    <n-modal
      v-model:show="showDetailModal"
      preset="card"
      :title="`插件详情 - ${currentPluginDetail?.name || ''}`"
      style="width: min(900px, 92vw)"
    >
      <n-descriptions
        v-if="currentPluginDetail"
        :column="1"
        bordered
        label-placement="left"
      >
        <n-descriptions-item label="ID">{{ currentPluginDetail.id }}</n-descriptions-item>
        <n-descriptions-item label="名称">{{ currentPluginDetail.name }}</n-descriptions-item>
        <n-descriptions-item label="版本">{{ currentPluginDetail.version || '-' }}</n-descriptions-item>
        <n-descriptions-item label="作者">{{ currentPluginDetail.author || '-' }}</n-descriptions-item>
        <n-descriptions-item label="许可证">{{ currentPluginDetail.license || '-' }}</n-descriptions-item>
        <n-descriptions-item label="描述">{{ currentPluginDetail.description || '-' }}</n-descriptions-item>
        <n-descriptions-item label="依赖服务">
          {{ (currentPluginDetail.meta?.depend_services || []).length ? currentPluginDetail.meta?.depend_services?.join(' , ') : '-' }}
        </n-descriptions-item>
        <n-descriptions-item label="引用了哪些插件">
          {{ currentPluginDetail.references.length ? currentPluginDetail.references.join(' , ') : '-' }}
        </n-descriptions-item>
        <n-descriptions-item label="被哪些插件引用">
          {{ currentPluginDetail.referents.length ? currentPluginDetail.referents.join(' , ') : '-' }}
        </n-descriptions-item>
        <n-descriptions-item label="主页">
          {{ currentPluginDetail.meta?.urls?.homepage || '-' }}
        </n-descriptions-item>
      </n-descriptions>

      <div v-if="currentPluginDetail?.meta?.readme" class="readme-wrapper">
        <div class="readme-title">README</div>
        <n-scrollbar style="max-height: 400px">
          <div class="markdown-body" v-html="renderedReadme"></div>
        </n-scrollbar>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import type { DataTableColumns } from 'naive-ui'

// Markdown 渲染（同步模式）
marked.setOptions({ async: false })

interface Plugin {
  id: string
  uid?: string | null
  name: string
  description: string
  version: string | null
  license?: string | null
  author: string
  enabled: boolean
  available?: boolean
  reusable?: boolean
  is_static?: boolean
  subplugins?: string[]
  path?: string
  configurable: boolean
  config: Record<string, any>
  references: string[]
  referents: string[]
  _toggling?: boolean
  meta?: {
    urls?: Record<string, string>
    readme?: string | null
    depend_services?: string[]
  }
}

const api = useApi()
const message = useMessage()

const loading = ref(false)
const plugins = ref<Plugin[]>([])
const searchText = ref('')

const showConfigDrawer = ref(false)
const currentPlugin = ref<Plugin | null>(null)
const configForm = ref<Record<string, any>>({})
const saving = ref(false)
const showDetailModal = ref(false)
const currentPluginDetail = ref<Plugin | null>(null)

// Markdown 渲染后的 README（仅客户端渲染）
const renderedReadme = computed(() => {
  const raw = currentPluginDetail.value?.meta?.readme
  if (!raw) return ''
  // DOMPurify 只能在客户端使用
  if (!import.meta.client) return raw
  try {
    const html = marked.parse(raw, { async: false }) as string
    return DOMPurify.sanitize(html)
  } catch (e) {
    console.error('Markdown render error:', e)
    return `<pre>${raw}</pre>`
  }
})

// 分页
const pagination = {
  pageSize: 10,
}

// 过滤后的插件列表
const filteredPlugins = computed(() => {
  if (!searchText.value) {
    return plugins.value
  }
  const search = searchText.value.toLowerCase()
  return plugins.value.filter(p =>
    p.name.toLowerCase().includes(search) ||
    p.id.toLowerCase().includes(search) ||
    p.description.toLowerCase().includes(search)
  )
})

// 表格列定义
const columns: DataTableColumns<Plugin> = [
  {
    title: '名称',
    key: 'name',
    width: 150,
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '版本',
    key: 'version',
    width: 100,
  },
  {
    title: '作者',
    key: 'author',
    width: 120,
  },
  {
    title: '状态',
    key: 'enabled',
    width: 80,
    render: (row) => {
      return h(
        resolveComponent('NSwitch') as any,
        {
          value: row.enabled,
          loading: row._toggling,
          onUpdateValue: (value: boolean) => togglePlugin(row, value),
        }
      )
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 240,
    render: (row) => {
      return h(resolveComponent('NSpace') as any, null, () => [
        row.configurable && h(
          resolveComponent('NButton') as any,
          {
            size: 'small',
            onClick: () => openConfig(row),
          },
          () => '配置'
        ),
        h(
          resolveComponent('NButton') as any,
          {
            size: 'small',
            onClick: () => reloadPlugin(row),
          },
          () => '重载'
        ),
        h(
          resolveComponent('NButton') as any,
          {
            size: 'small',
            onClick: () => openDetail(row),
          },
          () => '详情'
        ),
      ])
    },
  },
]

// 加载插件列表
const loadPlugins = async () => {
  loading.value = true
  try {
    const response = await api.get<Plugin[]>('/plugins')
    plugins.value = response
  } catch (e) {
    message.error('加载插件列表失败')
  } finally {
    loading.value = false
  }
}

// 切换插件状态
const togglePlugin = async (plugin: Plugin, enable: boolean) => {
  (plugin as any)._toggling = true

  try {
    const response = await api.post<{ success: boolean }>(`/plugins/${plugin.id}/toggle`, {
      enable,
    })

    if (response.success) {
      plugin.enabled = enable
      message.success(enable ? '插件已启用' : '插件已禁用')
    } else {
      message.error('操作失败')
    }
  } catch (e) {
    message.error('操作失败')
  } finally {
    (plugin as any)._toggling = false
  }
}

// 重载插件
const reloadPlugin = async (plugin: Plugin) => {
  try {
    const response = await api.post<{ success: boolean; message?: string }>(`/plugins/${plugin.id}/reload`)

    if (response.success) {
      message.success('插件已重载')
      await loadPlugins()
    } else {
      message.error(response.message || '重载失败')
    }
  } catch (e) {
    message.error('重载失败')
  }
}

// 打开配置
const openConfig = (plugin: Plugin) => {
  currentPlugin.value = plugin
  configForm.value = { ...plugin.config }
  showConfigDrawer.value = true
}

// 打开详情
const openDetail = async (plugin: Plugin) => {
  try {
    const response = await api.get<{ success: boolean; data: Plugin; message?: string }>(`/plugins/${plugin.id}`)
    if (response.success) {
      currentPluginDetail.value = response.data
      showDetailModal.value = true
    } else {
      message.error(response.message || '加载详情失败')
    }
  } catch {
    message.error('加载详情失败')
  }
}

// 保存配置
const saveConfig = async () => {
  if (!currentPlugin.value) return

  saving.value = true

  try {
    const response = await api.put<{ success: boolean; message?: string }>(
      `/plugins/${currentPlugin.value.id}/config`,
      { config: configForm.value }
    )

    if (response.success) {
      message.success('配置已保存')
      currentPlugin.value.config = { ...configForm.value }
      showConfigDrawer.value = false
    } else {
      message.error(response.message || '保存失败')
    }
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 初始化
onMounted(() => {
  loadPlugins()
})
</script>

<style scoped>
.plugins-page {
  max-width: 1200px;
  margin: 0 auto;
}

.readme-wrapper {
  margin-top: 16px;
  border: 1px solid var(--n-border-color);
  border-radius: 6px;
  padding: 16px;
}

.readme-title {
  font-weight: 600;
  margin-bottom: 12px;
}

/* Markdown 渲染样式 */
.markdown-body {
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body :deep(h1) {
  font-size: 1.5em;
  border-bottom: 1px solid var(--n-border-color);
  padding-bottom: 0.3em;
}

.markdown-body :deep(h2) {
  font-size: 1.3em;
  border-bottom: 1px solid var(--n-border-color);
  padding-bottom: 0.3em;
}

.markdown-body :deep(h3) {
  font-size: 1.1em;
}

.markdown-body :deep(p) {
  margin: 0.5em 0;
}

.markdown-body :deep(code) {
  background-color: var(--n-color-target);
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  background-color: var(--n-color-target);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.markdown-body :deep(li) {
  margin: 0.25em 0;
}

.markdown-body :deep(blockquote) {
  margin: 0.5em 0;
  padding: 0.5em 1em;
  border-left: 4px solid var(--n-border-color);
  color: var(--n-text-color-3);
}

.markdown-body :deep(a) {
  color: var(--n-text-color-info);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--n-border-color);
  padding: 6px 12px;
  text-align: left;
}

.markdown-body :deep(th) {
  background-color: var(--n-color-target);
  font-weight: 600;
}

.markdown-body :deep(img) {
  max-width: 100%;
  height: auto;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--n-border-color);
  margin: 1em 0;
}
</style>
