<template>
  <div class="additional-properties-editor">
    <n-space vertical style="width: 100%">
      <!-- 现有键值对 -->
      <n-card
        v-for="(value, key) in filteredModel"
        :key="key"
        size="small"
        closable
        @close="removeProperty(String(key))"
      >
        <template #header>
          <n-input
            :value="String(key)"
            size="small"
            style="width: 200px"
            placeholder="属性名"
            @update:value="(newKey: string) => renameProperty(String(key), newKey)"
          />
        </template>
        
        <!-- 有类型定义的值 -->
        <template v-if="valueSchema">
          <SchemaField
            :model-value="value"
            :field-schema="valueSchema"
            :defs="defs"
            :field-key="`additionalProp.${key}`"
            @update:model-value="updateProperty(String(key), $event)"
          />
        </template>
        
        <!-- 无类型定义，根据值类型推断 -->
        <template v-else>
          <template v-if="typeof value === 'boolean'">
            <n-switch
              :value="value"
              @update:value="updateProperty(String(key), $event)"
            />
          </template>
          <template v-else-if="typeof value === 'number'">
            <n-input-number
              :value="value"
              @update:value="updateProperty(String(key), $event)"
            />
          </template>
          <template v-else-if="typeof value === 'object' && value !== null">
            <n-input
              type="textarea"
              :value="JSON.stringify(value, null, 2)"
              :rows="3"
              @update:value="(v: string) => { try { updateProperty(String(key), JSON.parse(v)) } catch {} }"
            />
          </template>
          <template v-else>
            <n-input
              :value="String(value || '')"
              @update:value="updateProperty(String(key), $event)"
            />
          </template>
        </template>
      </n-card>

      <!-- 添加新属性 -->
      <n-space>
        <n-input
          v-model:value="newKey"
          placeholder="新属性名"
          style="width: 200px"
        />
        <n-button @click="addProperty" :disabled="!newKey">
          添加属性
        </n-button>
      </n-space>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  valueSchema?: any
  defs: Record<string, any>
  excludedKeys?: string[]
  modelValue?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  excludedKeys: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
}>()

const newKey = ref('')

// 过滤掉已定义的属性
const filteredModel = computed(() => {
  if (!props.modelValue) return {}
  const excluded = new Set(props.excludedKeys)
  const result: Record<string, any> = {}
  for (const [key, value] of Object.entries(props.modelValue)) {
    if (!excluded.has(key)) {
      result[key] = value
    }
  }
  return result
})

function updateProperty(key: string, value: any) {
  const newObj = { ...(props.modelValue || {}), [key]: value }
  emit('update:modelValue', newObj)
}

function removeProperty(key: string) {
  const newObj = { ...(props.modelValue || {}) }
  delete newObj[key]
  emit('update:modelValue', newObj)
}

function renameProperty(oldKey: string, newKey: string) {
  if (oldKey === newKey || !newKey) return
  const newObj: Record<string, any> = {}
  for (const [key, value] of Object.entries(props.modelValue || {})) {
    if (key === oldKey) {
      newObj[newKey] = value
    } else {
      newObj[key] = value
    }
  }
  emit('update:modelValue', newObj)
}

function addProperty() {
  if (!newKey.value) return
  
  let defaultValue: any = ''
  if (props.valueSchema) {
    if (props.valueSchema.type === 'object') {
      defaultValue = {}
    } else if (props.valueSchema.type === 'array') {
      defaultValue = []
    } else if (props.valueSchema.type === 'boolean') {
      defaultValue = false
    } else if (props.valueSchema.type === 'number' || props.valueSchema.type === 'integer') {
      defaultValue = 0
    }
  }
  
  const newObj = { ...(props.modelValue || {}), [newKey.value]: defaultValue }
  emit('update:modelValue', newObj)
  newKey.value = ''
}
</script>

<style scoped>
.additional-properties-editor {
  width: 100%;
}
</style>
