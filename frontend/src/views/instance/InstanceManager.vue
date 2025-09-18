<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  listInstances,
  createInstance,
  startInstance as apiStartInstance,
  stopInstance as apiStopInstance,
  deleteInstance,
  updateInstanceConfig,
  type InstanceItem
} from '@/api/instances'

const instances = ref<InstanceItem[]>([])
const loading = ref(false)
const operationLoading = reactive<Record<string, boolean>>({})

// 创建实例
const showCreateDialog = ref(false)
const createLoading = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  name: '',
  configJson: ''
})

const createRules: FormRules = {
  name: [
    { required: true, message: '请输入实例名称', trigger: 'blur' },
    { min: 2, max: 50, message: '实例名称长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

// 配置管理
const showConfigDialog = ref(false)
const configLoading = ref(false)
const currentInstance = ref<InstanceItem | null>(null)
const configForm = reactive({
  configJson: ''
})

// 获取实例列表
async function fetchInstances() {
  loading.value = true
  try {
    instances.value = await listInstances()
  } catch (error) {
    console.error('获取实例列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 创建实例
async function handleCreate() {
  const valid = await createFormRef.value?.validate()
  if (!valid) return

  createLoading.value = true
  try {
    let config = undefined
    if (createForm.configJson.trim()) {
      config = JSON.parse(createForm.configJson)
    }

    await createInstance({
      name: createForm.name,
      config
    })

    ElMessage.success('实例创建成功')
    showCreateDialog.value = false
    createForm.name = ''
    createForm.configJson = ''
    fetchInstances()
  } catch (error) {
    console.error('创建实例失败:', error)
    if (error instanceof SyntaxError) {
      ElMessage.error('配置JSON格式错误')
    }
  } finally {
    createLoading.value = false
  }
}

// 启动实例
async function startInstance(id: number) {
  operationLoading[id] = true
  try {
    await apiStartInstance(id)
    ElMessage.success('实例启动成功')
    fetchInstances()
  } catch (error) {
    console.error('启动实例失败:', error)
  } finally {
    operationLoading[id] = false
  }
}

// 停止实例
async function stopInstance(id: number) {
  operationLoading[id] = true
  try {
    await apiStopInstance(id)
    ElMessage.success('实例停止成功')
    fetchInstances()
  } catch (error) {
    console.error('停止实例失败:', error)
  } finally {
    operationLoading[id] = false
  }
}

// 删除实例确认
async function confirmDelete(instance: InstanceItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除实例 "${instance.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteInstance(instance.id)
    ElMessage.success('实例删除成功')
    fetchInstances()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除实例失败:', error)
    }
  }
}

// 打开配置对话框
function openConfig(instance: InstanceItem) {
  currentInstance.value = instance
  configForm.configJson = JSON.stringify(instance.config || {}, null, 2)
  showConfigDialog.value = true
}

// 更新配置
async function handleUpdateConfig() {
  if (!currentInstance.value) return

  configLoading.value = true
  try {
    const config = JSON.parse(configForm.configJson)
    await updateInstanceConfig(currentInstance.value.id, config)
    ElMessage.success('配置更新成功')
    showConfigDialog.value = false
    fetchInstances()
  } catch (error) {
    console.error('更新配置失败:', error)
    if (error instanceof SyntaxError) {
      ElMessage.error('配置JSON格式错误')
    }
  } finally {
    configLoading.value = false
  }
}

// 打开日志（跳转到控制台页面）
function openLogs(instance: InstanceItem) {
  // 这里可以跳转到控制台页面，并传递实例ID
  ElMessage.info(`查看实例 ${instance.name} 的日志`)
}

// 工具函数
function getStatusType(status: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' {
  const types: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    running: 'success',
    stopped: 'info',
    starting: 'warning',
    stopping: 'warning'
  }
  return types[status] || 'info'
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    running: '运行中',
    stopped: '已停止',
    starting: '启动中',
    stopping: '停止中'
  }
  return texts[status] || status
}

function formatTime(time: string) {
  return new Date(time).toLocaleString()
}

onMounted(() => {
  fetchInstances()
})
</script>

<template>
  <div class="instance-manager">
    <el-card shadow="hover">
      <template #header>
        <div class="header-content">
          <div>
            <h1>实例管理</h1>
            <p>管理 Entari 实例的创建、启动和配置</p>
          </div>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon>
              <Plus />
            </el-icon>
            创建实例
          </el-button>
        </div>
      </template>

      <!-- 实例列表 -->
      <el-table :data="instances" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="实例名称" min-width="150" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.state)">
              {{ getStatusText(row.state) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="资源使用" width="200">
          <template #default="{ row }">
            <div v-if="row.stats">
              <div>CPU: {{ row.stats.cpu }}%</div>
              <div>内存: {{ row.stats.memory }}MB</div>
            </div>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300">
          <template #default="{ row }">
            <el-button-group>
              <el-button v-if="row.status === 'stopped'" size="small" type="success" @click="startInstance(row.id)"
                :loading="operationLoading[row.id]">
                启动
              </el-button>
              <el-button v-if="row.status === 'running'" size="small" type="warning" @click="stopInstance(row.id)"
                :loading="operationLoading[row.id]">
                停止
              </el-button>
              <el-button size="small" @click="openConfig(row)">
                配置
              </el-button>
              <el-button size="small" @click="openLogs(row)">
                日志
              </el-button>
              <el-button size="small" type="danger" @click="confirmDelete(row)" :disabled="row.status === 'running'">
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建实例对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建新实例" width="500">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100">
        <el-form-item label="实例名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入实例名称" />
        </el-form-item>
        <el-form-item label="配置" prop="config">
          <el-input v-model="createForm.configJson" type="textarea" :rows="6" placeholder="请输入JSON格式的配置（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="createLoading">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 配置对话框 -->
    <el-dialog v-model="showConfigDialog" title="实例配置" width="600">
      <el-form :model="configForm" label-width="100">
        <el-form-item label="实例名称">
          <el-input :value="currentInstance?.name" disabled />
        </el-form-item>
        <el-form-item label="配置">
          <el-input v-model="configForm.configJson" type="textarea" :rows="8" placeholder="请输入JSON格式的配置" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateConfig" :loading="configLoading">
          保存配置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.instance-manager {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

h1 {
  margin: 0;
  font-size: 24px;
}

.text-gray-400 {
  color: #9ca3af;
}
</style>
