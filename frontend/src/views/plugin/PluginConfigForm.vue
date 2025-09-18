<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { PluginItem, PluginConfig } from '@/api/plugin'
import { savePlugin } from '@/api/plugin'

const props = defineProps<{
    modelValue: boolean
    plugin: PluginItem | null
}>()

const emit = defineEmits<{
    (e: 'update:modelValue', v: boolean): void
    (e: 'closed'): void
    (e: 'saved'): void
}>()

const visible = computed<boolean>({
    get: () => props.modelValue,
    set: (v) => emit('update:modelValue', v),
})

const strConfig = ref<Record<string, string>>({})
const originalType = ref<Record<string, string>>({})

function configToString(cfg: PluginConfig) {
    const str: Record<string, string> = {}
    const types: Record<string, string> = {}
    Object.entries(cfg).forEach(([k, v]) => {
        types[k] = Array.isArray(v) ? 'array' : typeof v
        str[k] = v == null ? '' : String(v)
    })
    strConfig.value = str
    originalType.value = types
}

watch(
    () => props.plugin,
    (val) => {
        if (val?.config) configToString(val.config)
        else {
            strConfig.value = {}
            originalType.value = {}
        }
    },
    { immediate: true },
)

function stringToConfig(): PluginConfig {
    const cfg: PluginConfig = {}
    Object.entries(strConfig.value).forEach(([k, v]) => {
        const type = originalType.value[k]
        if (type === 'boolean') cfg[k] = v === 'true'
        else if (type === 'number') cfg[k] = Number(v)
        else if (type === 'array') cfg[k] = v.split(',').map((s) => s.trim())
        else cfg[k] = v || undefined
    })
    return cfg
}

async function save() {
    if (!props.plugin) return
    try {
        const newConfig = stringToConfig()
        await savePlugin({ id: props.plugin.id, config: newConfig })

        //eslint-disable-next-line vue/no-mutating-props
        if (props.plugin) props.plugin.config = newConfig

        ElMessage.success('配置已保存')
        emit('saved')
        visible.value = false
    } catch (e) {
        ElMessage.error(`保存失败：${(e as Error).message}`)
    }
}
</script>

<template>
    <el-drawer v-model="visible" :title="`配置插件：${props.plugin?.title ?? ''}`" direction="rtl" size="40%"
        @close="emit('closed')">
        <el-form v-if="strConfig" label-width="120px">
            <el-form-item v-for="(val, key) in strConfig" :key="key" :label="String(key)">
                <!-- 布尔值 -->
                <el-switch v-if="originalType[key] === 'boolean'" v-model="strConfig[key]" active-value="true"
                    inactive-value="false" />
                <!-- 其它类型 -->
                <el-input v-else v-model="strConfig[key]" :key="key" :disabled="key === '$path'" />
            </el-form-item>

            <el-form-item>
                <el-button type="primary" @click="save">保存</el-button>
                <el-button @click="visible = false">取消</el-button>
            </el-form-item>
        </el-form>
    </el-drawer>
</template>