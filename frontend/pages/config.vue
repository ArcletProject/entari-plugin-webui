<template>
  <div class="config-page">
    <n-grid :cols="24" :x-gap="16">
      <!-- 左侧导航 -->
      <n-gi :span="5">
        <n-card title="配置项" size="small">
          <n-menu
            :options="menuOptions"
            :value="activeSection"
            @update:value="handleSectionChange"
          />
        </n-card>
      </n-gi>

      <!-- 右侧表单 -->
      <n-gi :span="19">
        <n-card :title="currentSectionTitle" size="small">
          <template #header-extra>
            <n-space>
              <n-button size="small" @click="loadSectionData">
                <template #icon>
                  <Icon name="mdi:refresh" />
                </template>
                刷新
              </n-button>
              <n-button type="primary" size="small" :loading="saving" @click="saveSection">
                <template #icon>
                  <Icon name="mdi:content-save" />
                </template>
                保存
              </n-button>
            </n-space>
          </template>

          <n-spin :show="loading">
            <!-- 动态表单 -->
            <n-form v-if="sectionData" :model="formData" label-placement="left" label-width="140">
              <DynamicConfigForm
                v-model="formData"
                :schema="currentSchema"
              />
            </n-form>

            <n-empty v-else description="请选择配置项" />
          </n-spin>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import type { MenuOption } from 'naive-ui'

const api = useApi()
const message = useMessage()

const loading = ref(false)
const saving = ref(false)
const activeSection = ref('basic')
const sectionData = ref<any>(null)
const formData = ref<any>({})
const sections = ref<string[]>([])
const pluginSections = ref<string[]>([])
const currentSchema = ref<any>(null)

// 菜单选项
const menuOptions = computed<MenuOption[]>(() => {
  const options: MenuOption[] = [
    {
      label: '基础配置',
      key: 'basic',
      icon: () => h(resolveComponent('Icon') as any, { name: 'mdi:cog' }),
    },
  ]

  // 添加插件配置（作为一级菜单，用 type='group' 做分组标题）
  if (pluginSections.value.length > 0) {
    options.push({
      type: 'group',
      label: '插件配置',
      key: 'plugin-header',
      children: pluginSections.value.map(section => {
        const name = section.replace('plugins.', '')
        return {
          label: name,
          key: section,
          icon: () => h(resolveComponent('Icon') as any, { name: 'mdi:puzzle-outline', size: '18' }),
        }
      }),
    })
  }

  return options
})

// 当前节标题
const currentSectionTitle = computed(() => {
  if (activeSection.value === 'basic') {
    return '基础配置'
  }
  return activeSection.value.replace('plugins.', '插件配置 - ')
})

// 加载配置概览
const loadConfig = async () => {
  try {
    const response = await api.get<{
      success: boolean
      sections: string[]
      plugin_sections: string[]
    }>('/config')

    if (response.success) {
      sections.value = response.sections
      pluginSections.value = response.plugin_sections
    }
  } catch (e) {
    message.error('加载配置失败')
  }
}

// 加载指定节的数据
const loadSectionData = async () => {
  loading.value = true

  try {
    // 加载数据
    const dataResponse = await api.get<{
      success: boolean
      data: any
    }>(`/config/${activeSection.value}`)

    if (dataResponse.success) {
      sectionData.value = dataResponse.data
      formData.value = JSON.parse(JSON.stringify(dataResponse.data))
    }

    // 加载 schema
    const schemaResponse = await api.get<{
      success: boolean
      schema: any
    }>(`/config/schema/${activeSection.value}`)

    if (schemaResponse.success) {
      currentSchema.value = schemaResponse.schema
    }
  } catch (e) {
    message.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

// 切换节
const handleSectionChange = (key: string) => {
  activeSection.value = key
  loadSectionData()
}

// 保存配置
const saveSection = async () => {
  saving.value = true

  try {
    const response = await api.put<{
      success: boolean
      message?: string
    }>(`/config/${activeSection.value}`, {
      data: formData.value,
    })

    if (response.success) {
      message.success('保存成功')
      sectionData.value = JSON.parse(JSON.stringify(formData.value))
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
onMounted(async () => {
  await loadConfig()
  await loadSectionData()
})
</script>

<style scoped>
.config-page {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
