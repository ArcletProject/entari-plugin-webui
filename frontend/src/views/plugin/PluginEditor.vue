<template>
  <div class="editor">
    <el-form :model="form" label-width="100">
      <el-form-item label="插件名称">
        <el-input v-model="form.name" placeholder="仅支持字母、数字、下划线" />
      </el-form-item>
      <el-form-item label="版本">
        <el-input v-model="form.version" placeholder="0.1.0" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.desc" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="主入口">
        <el-input v-model="form.entry" placeholder="__init__.py" />
      </el-form-item>
      <el-form-item label="代码">
        <el-input v-model="form.code" type="textarea" :rows="16" spellcheck="false" placeholder="在此输入插件代码" />
      </el-form-item>
    </el-form>

    <div class="actions">
      <el-button type="primary" @click="save">保存</el-button>
      <el-button @click="reload">保存并热重载</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { savePlugin } from '@/api/plugin'
import { ElMessage } from 'element-plus'

interface PluginItem {
  name: string
  version: string
  desc: string
  entry?: string
  code?: string
}

const props = defineProps<{ plugin: Partial<PluginItem> }>()
const emit = defineEmits(['save', 'reload'])

const form = ref({
  name: '',
  version: '0.1.0',
  desc: '',
  entry: '__init__.py',
  code: '',
})

watch(
  () => props.plugin,
  (p) => {
    form.value = {
      name: p.name || '',
      version: p.version || '0.1.0',
      desc: p.desc || '',
      entry: p.entry || '__init__.py',
      code: p.code || ''
    }
  },
  { immediate: true }
)

async function save() {
  try {
    await savePlugin(form.value)
    ElMessage.success('已保存')
    emit('save')
  } catch (error) {
    console.error('保存插件失败:', error)
    ElMessage.error('保存插件失败')
  }
}

async function reload() {
  try {
    await savePlugin(form.value)
    ElMessage.success('已保存并热重载')
    emit('reload', form.value.name)
  } catch (error) {
    console.error('保存并重载插件失败:', error)
    ElMessage.error('保存并重载插件失败')
  }
}
</script>

<style scoped>
.editor {
  padding: 0 16px;
}

.actions {
  margin-top: 16px;
  text-align: right;
}
</style>
