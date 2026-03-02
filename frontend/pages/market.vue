<template>
  <div class="market-page">
    <n-card title="插件市场">
      <template #header-extra>
        <n-space>
          <n-select
            v-model:value="selectedTag"
            :options="tagOptions"
            placeholder="按标签筛选"
            clearable
            style="width: 150px"
          />
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
        </n-space>
      </template>

      <n-spin :show="loading">
        <n-grid :cols="3" :x-gap="16" :y-gap="16">
          <n-gi v-for="plugin in filteredPlugins" :key="plugin.name">
            <n-card hoverable>
              <template #header>
                <n-space align="center">
                  <Icon name="mdi:puzzle" size="20" />
                  <span>{{ plugin.name }}</span>
                </n-space>
              </template>

              <template #header-extra>
                <n-tag v-if="plugin.installed" type="success" size="small">
                  已安装
                </n-tag>
              </template>

              <n-ellipsis :line-clamp="2" style="min-height: 42px">
                {{ plugin.description }}
              </n-ellipsis>

              <n-space style="margin-top: 12px">
                <n-tag
                  v-for="tag in plugin.tags"
                  :key="tag"
                  size="small"
                  round
                >
                  {{ tag }}
                </n-tag>
              </n-space>

              <template #footer>
                <n-space justify="space-between" align="center">
                  <n-text depth="3">v{{ plugin.version }}</n-text>

                  <n-space>
                    <n-button
                      v-if="plugin.homepage"
                      size="small"
                      tag="a"
                      :href="plugin.homepage"
                      target="_blank"
                    >
                      <template #icon>
                        <Icon name="mdi:open-in-new" />
                      </template>
                    </n-button>

                    <n-button
                      v-if="plugin.installed"
                      size="small"
                      type="error"
                      :loading="plugin._uninstalling"
                      @click="uninstallPlugin(plugin)"
                    >
                      卸载
                    </n-button>
                    <n-button
                      v-else
                      size="small"
                      type="primary"
                      :loading="plugin._installing"
                      @click="installPlugin(plugin)"
                    >
                      安装
                    </n-button>
                  </n-space>
                </n-space>
              </template>
            </n-card>
          </n-gi>
        </n-grid>

        <n-empty v-if="filteredPlugins.length === 0 && !loading" description="暂无插件" />
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
interface MarketPlugin {
  name: string
  description: string
  version: string
  author: string
  tags: string[]
  homepage?: string
  installed: boolean
  _installing?: boolean
  _uninstalling?: boolean
}

const api = useApi()
const message = useMessage()

const loading = ref(false)
const plugins = ref<MarketPlugin[]>([])
const searchText = ref('')
const selectedTag = ref<string | null>(null)

// 获取所有标签
const tagOptions = computed(() => {
  const tags = new Set<string>()
  plugins.value.forEach(p => p.tags.forEach(t => tags.add(t)))
  return Array.from(tags).map(t => ({ label: t, value: t }))
})

// 过滤后的插件
const filteredPlugins = computed(() => {
  let result = plugins.value

  if (selectedTag.value) {
    result = result.filter(p => p.tags.includes(selectedTag.value!))
  }

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(p =>
      p.name.toLowerCase().includes(search) ||
      p.description.toLowerCase().includes(search)
    )
  }

  return result
})

// 加载插件市场
const loadMarketPlugins = async () => {
  loading.value = true
  try {
    const response = await api.get<MarketPlugin[]>('/market/plugins')
    plugins.value = response
  } catch (e) {
    message.error('加载插件市场失败')
  } finally {
    loading.value = false
  }
}

// 安装插件
const installPlugin = async (plugin: MarketPlugin) => {
  plugin._installing = true

  try {
    const response = await api.post<{ success: boolean; task_id: string }>('/plugins/install', {
      name: plugin.name,
    })

    if (response.success) {
      message.info('正在安装...')
      // 轮询任务状态
      await pollTaskStatus(response.task_id, plugin, 'install')
    } else {
      message.error('安装失败')
    }
  } catch (e) {
    message.error('安装失败')
  } finally {
    plugin._installing = false
  }
}

// 卸载插件
const uninstallPlugin = async (plugin: MarketPlugin) => {
  plugin._uninstalling = true

  try {
    const response = await api.post<{ success: boolean; task_id: string }>('/plugins/uninstall', {
      name: plugin.name,
    })

    if (response.success) {
      message.info('正在卸载...')
      await pollTaskStatus(response.task_id, plugin, 'uninstall')
    } else {
      message.error('卸载失败')
    }
  } catch (e) {
    message.error('卸载失败')
  } finally {
    plugin._uninstalling = false
  }
}

// 轮询任务状态
const pollTaskStatus = async (taskId: string, plugin: MarketPlugin, action: 'install' | 'uninstall') => {
  const maxAttempts = 60 // 最多等待 60 秒
  let attempts = 0

  while (attempts < maxAttempts) {
    await new Promise(resolve => setTimeout(resolve, 1000))

    try {
      const status = await api.get<{
        success: boolean
        status: string
        message: string
      }>(`/plugins/task/${taskId}`)

      if (status.status === 'success') {
        plugin.installed = action === 'install'
        message.success(action === 'install' ? '安装成功' : '卸载成功')
        return
      } else if (status.status === 'failed') {
        message.error(status.message || (action === 'install' ? '安装失败' : '卸载失败'))
        return
      }
    } catch (e) {
      // 继续轮询
    }

    attempts++
  }

  message.warning('操作超时，请检查日志')
}

// 初始化
onMounted(() => {
  loadMarketPlugins()
})
</script>

<style scoped>
.market-page {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
