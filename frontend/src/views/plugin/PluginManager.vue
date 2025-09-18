<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PluginEditor from '@/views/plugin/PluginEditor.vue'
import { listPlugins, searchPlugins, loadPlugin, unloadPlugin, reloadPlugin, type PluginItem } from '@/api/plugin'

/* 数据 */
const searchKey = ref('')
const remoteList = ref<LocalPluginItem[]>([])
const localList = ref<LocalPluginItem[]>([])

/* 插件列表（本地 + 远程） */
const pluginTable = computed(() => {
  const arr = [...localList.value, ...remoteList.value]
  if (!searchKey.value) return arr
  return arr.filter((p) => p.name.includes(searchKey.value))
})

/* 抽屉 */
const drawer = ref(false)
const drawerTitle = ref('')
const editing = ref<Partial<LocalPluginItem>>({})

/* 方法 */
async function fetchLocal() {
  try {
    localList.value = await listPlugins()
  } catch (error) {
    console.error('获取本地插件列表失败:', error)
    ElMessage.error('获取本地插件列表失败')
  }
}

async function doSearch() {
  if (!searchKey.value) return
  try {
    remoteList.value = await searchPlugins(searchKey.value)
  } catch (error) {
    console.error('搜索插件失败:', error)
    ElMessage.error('搜索插件失败')
  }
}

function openNew() {
  editing.value = { name: '', desc: '', version: '0.1.0', local: true }
  drawerTitle.value = '新建插件'
  drawer.value = true
}

function openEditor(plugin: LocalPluginItem) {
  editing.value = { ...plugin }
  drawerTitle.value = `编辑 - ${plugin.name}`
  drawer.value = true
}

async function load(plugin: LocalPluginItem) {
  try {
    await loadPlugin(plugin.name)
    ElMessage.success(`${plugin.name} 已加载`)
    fetchLocal()
  } catch (error) {
    console.error('加载插件失败:', error)
    ElMessage.error(`加载插件 ${plugin.name} 失败`)
  }
}

async function unload(plugin: LocalPluginItem) {
  try {
    await unloadPlugin(plugin.name)
    ElMessage.success(`${plugin.name} 已卸载`)
    fetchLocal()
  } catch (error) {
    console.error('卸载插件失败:', error)
    ElMessage.error(`卸载插件 ${plugin.name} 失败`)
  }
}

async function reload(plugin: LocalPluginItem) {
  try {
    await reloadPlugin(plugin.name)
    ElMessage.success(`${plugin.name} 已热重载`)
    fetchLocal()
  } catch (error) {
    console.error('重载插件失败:', error)
    ElMessage.error(`重载插件 ${plugin.name} 失败`)
  }
}

/* 保存后刷新本地列表 */
async function handleSave() {
  drawer.value = false
  await fetchLocal()
}

/* 热重载当前插件 */
async function handleReload(name: string) {
  try {
    await reloadPlugin(name)
    ElMessage.success(`${name} 已热重载`)
  } catch (error) {
    console.error('热重载插件失败:', error)
    ElMessage.error(`热重载插件 ${name} 失败`)
  }
}

onMounted(() => {
  fetchLocal()
})

/* 扩展的本地插件类型 */
interface LocalPluginItem extends PluginItem {
  local?: boolean
}
</script>

<template>
  <div class="plugin-manager">
    <el-card shadow="hover">
      <template #header>
        <h1>插件管理</h1>
        <p>搜索、安装、开发与热重载 Entari 插件</p>
      </template>

      <!-- 搜索 & 安装 -->
      <section>
        <el-row :gutter="12">
          <el-col :span="16">
            <el-input v-model="searchKey" placeholder="在官方仓库搜索插件" clearable @keyup.enter="doSearch" />
          </el-col>
          <el-col :span="8">
            <el-button type="primary" @click="doSearch">搜索</el-button>
            <el-button @click="openNew">本地开发</el-button>
          </el-col>
        </el-row>
      </section>

      <!-- 插件列表 -->
      <section>
        <el-table :data="pluginTable" style="width: 100%">
          <el-table-column prop="name" label="名称" width="160" />
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column prop="desc" label="描述" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'loaded' ? 'success' : 'info'">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220">
            <template #default="{ row }">
              <el-button size="small" @click="openEditor(row)">编辑</el-button>
              <el-button v-if="row.status === 'loaded'" size="small" @click="reload(row)">重载</el-button>
              <el-button v-if="row.status === 'unloaded'" type="success" size="small" @click="load(row)">加载</el-button>
              <el-button v-else type="danger" size="small" @click="unload(row)">卸载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </el-card>

    <!-- 新建/编辑插件抽屉 -->
    <el-drawer v-model="drawer" :title="drawerTitle" direction="rtl" size="60%" destroy-on-close>
      <plugin-editor :plugin="editing" @save="handleSave" @reload="handleReload" />
    </el-drawer>
  </div>
</template>

<style scoped>
.plugin-manager {
  padding: 24px;
  max-width: 960px;
  margin: 0 auto;
  background: var(--pm-page-bg);
  transition: background 0.3s;
}

h1 {
  margin: 0;
  font-size: 24px;
  color: var(--pm-header-text);
  transition: color 0.3s;
}

section {
  margin-bottom: 24px;
  border-bottom: 1px solid var(--pm-section-divider);
  transition: border-color 0.3s;
}

:deep(.el-card) {
  background: var(--pm-card-bg);
  border: 1px solid var(--pm-card-border);
  box-shadow: 0 4px 12px var(--pm-card-shadow);
  transition: background 0.3s, border-color 0.3s, box-shadow 0.3s;
}

/* 表格 */
:deep(.el-table) {
  background: var(--pm-table-bg);
  color: var(--pm-section-text);
  transition: background 0.3s, color 0.3s;
}

:deep(.el-table th) {
  background: var(--pm-table-header-bg);
  color: var(--pm-section-text);
  border-bottom: 1px solid var(--pm-table-border);
}

:deep(.el-table td) {
  border-bottom: 1px solid var(--pm-table-border);
}

:deep(.el-table tr:hover) {
  background: var(--pm-table-hover);
}

:deep(.el-input__inner) {
  background: var(--pm-input-bg);
  border-color: var(--pm-input-border);
  color: var(--pm-input-text);
  transition: background 0.3s, border-color 0.3s, color 0.3s;
}

:deep(.el-button--primary) {
  background: var(--pm-btn-primary-bg);
  border-color: var(--pm-btn-primary-bg);
  color: var(--pm-btn-primary-text);
  transition: background 0.3s, border-color 0.3s, color 0.3s;
}

:deep(.el-button--primary:hover) {
  background: var(--pm-btn-primary-hover-bg, #5fa7ff);
  border-color: var(--pm-btn-primary-hover-bg, #5fa7ff);
}
</style>
