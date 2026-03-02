<template>
  <div class="schema-field">
    <!-- 解析 $ref 引用 -->
    <template v-if="resolvedSchema">
      <!-- 只读字段 -->
      <template v-if="resolvedSchema.readOnly">
        <n-input :value="String(modelValue || '')" disabled />
      </template>

      <!-- 布尔值 -->
      <template v-else-if="resolvedSchema.type === 'boolean'">
        <n-switch :value="modelValue" @update:value="emit('update:modelValue', $event)" />
      </template>

      <!-- 数字 -->
      <template v-else-if="resolvedSchema.type === 'number' || resolvedSchema.type === 'integer'">
        <n-input-number
          :value="modelValue"
          style="width: 200px"
          @update:value="emit('update:modelValue', $event)"
        />
      </template>

      <!-- 枚举选择 -->
      <template v-else-if="resolvedSchema.enum">
        <n-select
          :value="modelValue"
          :options="resolvedSchema.enum.map((e: any) => ({ label: String(e), value: e }))"
          style="width: 200px"
          @update:value="emit('update:modelValue', $event)"
        />
      </template>

      <!-- oneOf 多选类型 -->
      <template v-else-if="resolvedSchema.oneOf">
        <OneOfField
          :model-value="modelValue"
          :one-of="resolvedSchema.oneOf"
          :defs="defs"
          :field-key="fieldKey"
          @update:model-value="emit('update:modelValue', $event)"
        />
      </template>

      <!-- 数组 -->
      <template v-else-if="resolvedSchema.type === 'array'">
        <ArrayField
          :model-value="modelValue"
          :items-schema="resolvedSchema.items"
          :defs="defs"
          :field-key="fieldKey"
          @update:model-value="emit('update:modelValue', $event)"
        />
      </template>

      <!-- 对象 -->
      <template v-else-if="resolvedSchema.type === 'object'">
        <ObjectField
          :model-value="modelValue"
          :object-schema="resolvedSchema"
          :defs="defs"
          :field-key="fieldKey"
          @update:model-value="emit('update:modelValue', $event)"
        />
      </template>

      <!-- 字符串（默认） -->
      <template v-else>
        <n-input
          :value="modelValue"
          :type="resolvedSchema.format === 'password' ? 'password' : 'text'"
          @update:value="emit('update:modelValue', $event)"
        />
      </template>
    </template>

    <!-- 无法解析的 schema -->
    <template v-else>
      <n-input
        :value="typeof modelValue === 'object' ? JSON.stringify(modelValue) : String(modelValue || '')"
        @update:value="(v: string) => { try { emit('update:modelValue', JSON.parse(v)) } catch { emit('update:modelValue', v) } }"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  fieldSchema: any
  defs: Record<string, any>
  fieldKey: string
  modelValue?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

// 解析 $ref 引用
function resolveRef(schema: any, defs: Record<string, any>): any {
  if (!schema) return null
  
  if (schema.$ref) {
    // 解析 $ref 路径，如 "#/properties/basic/$defs/LogInfo"
    const refPath = schema.$ref
    const defsMatch = refPath.match(/\$defs\/([^/]+)$/)
    if (defsMatch && defs[defsMatch[1]]) {
      // 合并 $ref 解析结果和原 schema 的其他属性（如 description, title）
      const resolved = { ...defs[defsMatch[1]] }
      // 保留原 schema 中的 description 和 title
      if (schema.description) resolved.description = schema.description
      if (schema.title) resolved.title = schema.title
      return resolved
    }
    return null
  }
  
  return schema
}

const resolvedSchema = computed(() => {
  return resolveRef(props.fieldSchema, props.defs)
})
</script>

<style scoped>
.schema-field {
  width: 100%;
}
</style>
