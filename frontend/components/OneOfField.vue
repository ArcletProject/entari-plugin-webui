<template>
  <div class="oneof-field">
    <!-- 简单类型 oneOf（如 string | number | null） -->
    <template v-if="isSimpleOneOf">
      <n-input
        v-if="primaryType === 'string'"
        :value="modelValue ?? ''"
        :placeholder="hasNull ? '留空表示 null' : ''"
        @update:value="handleSimpleUpdate"
      />
      <n-input-number
        v-else-if="primaryType === 'number' || primaryType === 'integer'"
        :value="modelValue"
        style="width: 200px"
        @update:value="emit('update:modelValue', $event)"
      />
      <n-switch
        v-else-if="primaryType === 'boolean'"
        :value="modelValue"
        @update:value="emit('update:modelValue', $event)"
      />
      <n-input
        v-else
        :value="String(modelValue || '')"
        @update:value="emit('update:modelValue', $event)"
      />
    </template>

    <!-- 复杂类型 oneOf（如多个对象类型） -->
    <template v-else>
      <n-space vertical style="width: 100%">
        <n-select
          :value="selectedTypeIndex"
          :options="typeOptions"
          placeholder="选择类型"
          style="width: 200px"
          @update:value="handleTypeChange"
        />
        
        <template v-if="selectedTypeIndex !== null && selectedTypeIndex !== -1">
          <n-card size="small">
            <SchemaField
              :model-value="modelValue"
              :field-schema="resolvedOptions[selectedTypeIndex]"
              :defs="defs"
              :field-key="`${fieldKey}.oneOf`"
              @update:model-value="emit('update:modelValue', $event)"
            />
          </n-card>
        </template>
      </n-space>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface Props {
  oneOf: any[]
  defs: Record<string, any>
  fieldKey: string
  modelValue?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

// 解析 $ref
function resolveRef(schema: any, defs: Record<string, any>): any {
  if (!schema) return null
  if (schema.$ref) {
    const defsMatch = schema.$ref.match(/\$defs\/([^/]+)$/)
    if (defsMatch && defs[defsMatch[1]]) {
      return { ...defs[defsMatch[1]] }
    }
    return schema
  }
  return schema
}

// 解析所有 oneOf 选项
const resolvedOptions = computed(() => {
  return props.oneOf.map(opt => resolveRef(opt, props.defs))
})

// 判断是否为简单类型的 oneOf
const simpleTypes = ['string', 'number', 'integer', 'boolean', 'null']
const isSimpleOneOf = computed(() => {
  return resolvedOptions.value.every(opt => opt && simpleTypes.includes(opt.type))
})

// 获取主要类型（非 null 的第一个类型）
const primaryType = computed(() => {
  const nonNull = resolvedOptions.value.find(opt => opt?.type !== 'null')
  return nonNull?.type || 'string'
})

// 是否包含 null
const hasNull = computed(() => {
  return resolvedOptions.value.some(opt => opt?.type === 'null')
})

// 处理简单类型更新
function handleSimpleUpdate(value: string) {
  if (hasNull.value && value === '') {
    emit('update:modelValue', null)
  } else if (primaryType.value === 'number' || primaryType.value === 'integer') {
    emit('update:modelValue', Number(value) || 0)
  } else {
    emit('update:modelValue', value)
  }
}

// 复杂类型选择器
const typeOptions = computed(() => {
  return resolvedOptions.value.map((opt, index) => {
    if (opt?.type === 'null') {
      return { label: '空 (null)', value: -1 }
    }
    const label = opt?.title || opt?.type || `选项 ${index + 1}`
    return { label, value: index }
  })
})

// 当前选择的类型索引
const selectedTypeIndex = ref<number | null>(null)

// 根据当前值推断选中的类型
watch(() => props.modelValue, (val) => {
  if (val === null || val === undefined) {
    const nullIndex = resolvedOptions.value.findIndex(opt => opt?.type === 'null')
    selectedTypeIndex.value = nullIndex >= 0 ? -1 : null
  } else if (typeof val === 'object') {
    // 尝试匹配对象类型
    const matchIndex = resolvedOptions.value.findIndex(opt => {
      if (opt?.type !== 'object') return false
      // 检查是否有 type 字段匹配
      if (opt.properties?.type?.enum && val.type) {
        return opt.properties.type.enum.includes(val.type)
      }
      return true
    })
    selectedTypeIndex.value = matchIndex >= 0 ? matchIndex : 0
  } else {
    selectedTypeIndex.value = 0
  }
}, { immediate: true })

// 处理类型切换
function handleTypeChange(index: number) {
  selectedTypeIndex.value = index
  if (index === -1) {
    emit('update:modelValue', null)
  } else {
    const schema = resolvedOptions.value[index]
    if (schema?.type === 'object') {
      emit('update:modelValue', {})
    } else if (schema?.type === 'array') {
      emit('update:modelValue', [])
    } else if (schema?.type === 'boolean') {
      emit('update:modelValue', false)
    } else if (schema?.type === 'number' || schema?.type === 'integer') {
      emit('update:modelValue', 0)
    } else {
      emit('update:modelValue', '')
    }
  }
}
</script>

<style scoped>
.oneof-field {
  width: 100%;
}
</style>
