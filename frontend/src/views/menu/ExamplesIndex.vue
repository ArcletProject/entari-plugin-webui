<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth';

const dialogVisible = ref(false)
const instanceForm = ref({
    id: 0,
    name: 'config',
    type: 'ws',
    host: '127.0.0.1',
    port: 5140,
    path: 'satori',
    ignoreSelfMessage: true,
    logLevel: 'INFO',
    prefix: '/',
    autoReload: true,
    echo: true,
    inspect: true
})

const authStore = useAuthStore()
const networkTypes = ref(['ws', 'websocket', 'wh', 'webhook'])
const logLevels = ref(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

const generatedYaml = computed(() => {
    return `basic:
  network:
    - type: ${instanceForm.value.type}
      host: "${instanceForm.value.host}"
      port: ${instanceForm.value.port}
      path: "${instanceForm.value.path}"
  ignore_self_message: ${instanceForm.value.ignoreSelfMessage}
  log_level: ${instanceForm.value.logLevel}
  prefix: ["${instanceForm.value.prefix}"]
plugins:
  $prelude:
    - ::auto_reload
  .record_message: {}
  ::auto_reload:
    watch_dirs: ["."]
  ::echo: ${instanceForm.value.echo ? '{}' : 'false'}
  ::inspect: ${instanceForm.value.inspect ? '{}' : 'false'}
`
})

const handleConfirm = async () => {
    if (!instanceForm.value.id) {
        ElMessage.error('请填写实例ID')
        return
    }

    if (!instanceForm.value.name) {
        ElMessage.error('请填写实例名称')
        return
    }

    const requestData = {
        id: instanceForm.value.id,
        name: instanceForm.value.name,
        type: instanceForm.value.type,
        host: instanceForm.value.host,
        port: instanceForm.value.port,
        path: instanceForm.value.path,

        data: generatedYaml.value,
        filename: `${instanceForm.value.name}.yml`
    }

    try {
        await axios.post(
            'http://127.0.0.1:5140/api/menus',
            requestData,
            { headers: { 'Content-Type': 'application/json' } }
        )

        ElMessage.success('实例创建成功')

        authStore.addInstance({
            id: instanceForm.value.id,
            name: instanceForm.value.name,
            type: instanceForm.value.type,
            host: instanceForm.value.host,
            port: instanceForm.value.port,
            state: '已停止',
            path: instanceForm.value.path
        })
        dialogVisible.value = false
    } catch (error) {
        console.error('创建实例失败:', error)
        ElMessage.error('创建实例失败，请检查后端服务')
    }
}

const resetForm = () => {
    instanceForm.value = {
        id: 0,
        name: 'config',
        type: 'ws',
        host: '127.0.0.1',
        port: 5140,
        path: 'satori',
        ignoreSelfMessage: true,
        logLevel: 'INFO',
        prefix: '/',
        autoReload: true,
        echo: true,
        inspect: true
    }
}

const openDialog = () => {
    resetForm()
    dialogVisible.value = true
}
</script>

<template>
    <el-card>
        <template #header>
            <span class="card-header">
                <p>实例概览</p>
                <el-button @click="openDialog">添加实例</el-button>
            </span>
        </template>

        <el-table :data="authStore.instances" style="width: 100%" empty-text="暂无实例">
            <el-table-column prop="id" label="实例ID" width="120" />
            <el-table-column prop="name" label="实例名称" width="150" />
            <el-table-column prop="type" label="网络类型" width="120" />
            <el-table-column prop="host" label="服务器地址" />
            <el-table-column prop="port" label="端口" width="100" />
            <el-table-column prop="path" label="路径" width="120" />
            <el-table-column prop="state" label="状态" width="100">
                <template #default="{ row }">
                    <el-tag :type="row.state === '运行中' ? 'success' : 'danger'">
                        {{ row.state }}
                    </el-tag>
                </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
                <template #default>
                    <el-button size="small">启动</el-button>
                </template>
            </el-table-column>
        </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="添加实例" width="60vw">
        <el-form :model="instanceForm" label-width="120px">
            <el-form-item label="实例ID" required>
                <el-input v-model="instanceForm.id" placeholder="请输入唯一实例ID" style="width: 300px;" />
            </el-form-item>

            <el-form-item label="实例名称">
                <el-input v-model="instanceForm.name" placeholder="请输入实例名称" style="width: 300px;" />
            </el-form-item>

            <el-divider>网络配置</el-divider>

            <el-form-item label="网络类型">
                <el-select v-model="instanceForm.type" placeholder="请选择网络类型">
                    <el-option v-for="type in networkTypes" :key="type" :label="type" :value="type" />
                </el-select>
            </el-form-item>

            <el-form-item label="主机地址">
                <el-input v-model="instanceForm.host" placeholder="请输入主机地址" />
            </el-form-item>

            <el-form-item label="端口号">
                <el-input-number v-model="instanceForm.port" :min="1" :max="65535" />
            </el-form-item>

            <el-form-item label="路径">
                <el-input v-model="instanceForm.path" placeholder="请输入路径" />
            </el-form-item>

            <el-divider>基础配置</el-divider>

            <el-form-item label="忽略自身消息">
                <el-switch v-model="instanceForm.ignoreSelfMessage" />
            </el-form-item>

            <el-form-item label="日志级别">
                <el-select v-model="instanceForm.logLevel" placeholder="请选择日志级别">
                    <el-option v-for="level in logLevels" :key="level" :label="level" :value="level" />
                </el-select>
            </el-form-item>

            <el-form-item label="指令前缀">
                <el-input v-model="instanceForm.prefix" placeholder="请输入指令前缀" />
            </el-form-item>

            <el-divider>插件配置</el-divider>

            <el-form-item label="自动重载插件">
                <el-switch v-model="instanceForm.autoReload" />
            </el-form-item>

            <el-form-item label="Echo插件">
                <el-switch v-model="instanceForm.echo" />
            </el-form-item>

            <el-form-item label="Inspect插件">
                <el-switch v-model="instanceForm.inspect" />
            </el-form-item>

            <el-divider>生成的YML配置</el-divider>

            <el-form-item>
                <el-input v-model="generatedYaml" type="textarea" :rows="10" readonly style="font-family: monospace;" />
            </el-form-item>
        </el-form>

        <template #footer>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleConfirm">创建实例</el-button>
        </template>
    </el-dialog>
</template>

<style lang="scss" scoped>
.el-card {
    margin: 30px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;

    p {
        font-size: 20px;
        margin: 0;
    }
}

.el-divider {
    margin: 20px 0;
}

.el-form-item {
    margin-bottom: 18px;
}

:deep(.el-textarea__inner) {
    font-family: monospace;
    font-size: 12px;
    line-height: 1.5;
}
</style>