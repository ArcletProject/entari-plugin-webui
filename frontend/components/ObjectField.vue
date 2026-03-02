<template>
  <div class="object-field">
    <!-- 有 properties 定义的对象 -->
    <template v-if="objectSchema.properties">
      <n-form-item
        v-for="(propSchema, key) in objectSchema.properties"
        :key="key"
        :label="propSchema.title || String(key)"
        :show-require-mark="isRequired(String(key))"
      >
        <template #label>
          <n-space align="center" :size="4">
            <span>{{ propSchema.title || String(key) }}</span>
            <n-tooltip v-if="propSchema.description" trigger="hover">
              <template #trigger>
                <n-icon size="14" style="opacity: 0.6; cursor: help;">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm-1-7v2h2v-2h-2zm2-1.645A3.502 3.502 0 0 0 12 6.5a3.501 3.501 0 0 0-3.433 2.813l1.962.393A1.5 1.5 0 1 1 12 11.5a1 1 0 0 0-1 1V14h2v-.645z"/>
                  </svg>
                </n-icon>
              </template>
              {{ propSchema.description }}
            </n-tooltip>
          </n-space>
        </template>

        <SchemaField
          :model-value="(modelValue || {})[key]"
          :field-schema="propSchema"
          :defs="defs"
          :field-key="`${fieldKey}.${key}`"
          @update:model-value="updateProperty(String(key), $event)"
        />
      </n-form-item>

      <!-- additionalProperties 动态属性 -->
      <template v-if="objectSchema.additionalProperties && objectSchema.additionalProperties !== false">
        <n-divider v-if="hasExtraProperties">其他属性</n-divider>
        <AdditionalPropertiesEditor
          v-if="hasExtraProperties || objectSchema.additionalProperties === true"
          :model-value="extraProperties"
          :value-schema="objectSchema.additionalProperties === true ? null : objectSchema.additionalProperties"
          :defs="defs"
          :excluded-keys="Object.keys(objectSchema.properties || {})"
          @update:model-value="updateExtraProperties"
        />
      </template>
    </template>

    <!-- 只有 additionalProperties 的对象（动态键值对） -->
    <template v-else-if="objectSchema.additionalProperties">
      <AdditionalPropertiesEditor
        :model-value="modelValue || {}"
        :value-schema="objectSchema.additionalProperties === true ? null : objectSchema.additionalProperties"
        :defs="defs"
        @update:model-value="emit('update:modelValue', $event)"
      />
    </template>

    <!-- 完全无 schema 的对象 -->
    <template v-else>
      <n-input
        type="textarea"
        :value="JSON.stringify(modelValue || {}, null, 2)"
        :rows="4"
        @update:value="handleJsonUpdate"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  objectSchema: any
  defs: Record<string, any>
  fieldKey: string
  modelValue?: Record<string, any>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
}>()

// 检查字段是否必填
function isRequired(key: string): boolean {
  return props.objectSchema.required?.includes(key) || false
}

// 更新属性
function updateProperty(key: string, value: any) {
  const newObj = { ...(props.modelValue || {}), [key]: value }
  emit('update:modelValue', newObj)
}

// 额外属性（不在 properties 中定义的）
const extraProperties = computed(() => {
  if (!props.modelValue || !props.objectSchema.properties) return {}
  const definedKeys = new Set(Object.keys(props.objectSchema.properties))
  const extra: Record<string, any> = {}
  for (const [key, value] of Object.entries(props.modelValue)) {
    if (!definedKeys.has(key)) {
      extra[key] = value
    }
  }
  return extra
})

const hasExtraProperties = computed(() => {
  return Object.keys(extraProperties.value).length > 0
})

// 更新额外属性
function updateExtraProperties(extra: Record<string, any>) {
  const definedKeys = new Set(Object.keys(props.objectSchema.properties || {}))
  const newObj: Record<string, any> = {}
  
  // 保留定义的属性
  for (const [key, value] of Object.entries(props.modelValue || {})) {
    if (definedKeys.has(key)) {
      newObj[key] = value
    }
  }
  
  // 合并额外属性
  Object.assign(newObj, extra)
  emit('update:modelValue', newObj)
}

function handleJsonUpdate(value: string) {
  try {
    emit('update:modelValue', JSON.parse(value))
  } catch {
    // 忽略无效 JSON
  }
}
</script>

<style scoped>
.object-field {
  width: 100%;
}

.object-field :deep(.n-form-item) {
  margin-bottom: 12px;
}
</style>
