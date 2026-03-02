<template>
  <div class="array-field">
    <!-- 简单字符串数组 -->
    <template v-if="isSimpleStringArray">
      <n-dynamic-input
        :value="modelValue || []"
        placeholder="输入值"
        @update:value="emit('update:modelValue', $event)"
      />
    </template>

    <!-- 简单数字数组 -->
    <template v-else-if="isSimpleNumberArray">
      <n-dynamic-input
        :value="(modelValue || []).map(String)"
        placeholder="输入数字"
        @update:value="(v: any) => emit('update:modelValue', (v as string[]).map(Number))"
      />
    </template>

    <!-- oneOf 数组（如 network 配置） -->
    <template v-else-if="hasOneOf">
      <n-space vertical style="width: 100%">
        <n-card
          v-for="(item, index) in (modelValue || [])"
          :key="index"
          size="small"
          closable
          @close="removeItem(index)"
        >
          <template #header>
            <span>{{ getItemTitle(item, index) }}</span>
          </template>
          <OneOfField
            :model-value="item"
            :one-of="itemsSchema.oneOf"
            :defs="defs"
            :field-key="`${fieldKey}[${index}]`"
            @update:model-value="updateItem(index, $event)"
          />
        </n-card>
        
        <n-dropdown :options="addOptions" @select="handleAdd">
          <n-button dashed style="width: 100%">
            <template #icon><n-icon><AddIcon /></n-icon></template>
            添加项目
          </n-button>
        </n-dropdown>
      </n-space>
    </template>

    <!-- 复杂对象数组 -->
    <template v-else-if="isObjectArray">
      <n-space vertical style="width: 100%">
        <n-card
          v-for="(item, index) in (modelValue || [])"
          :key="index"
          size="small"
          closable
          @close="removeItem(index)"
        >
          <template #header>
            <span>项目 {{ index + 1 }}</span>
          </template>
          <ObjectField
            :model-value="item"
            :object-schema="resolvedItemsSchema"
            :defs="defs"
            :field-key="`${fieldKey}[${index}]`"
            @update:model-value="updateItem(index, $event)"
          />
        </n-card>
        
        <n-button dashed style="width: 100%" @click="addObjectItem">
          <template #icon><n-icon><AddIcon /></n-icon></template>
          添加项目
        </n-button>
      </n-space>
    </template>

    <!-- 默认：JSON 编辑 -->
    <template v-else>
      <n-input
        type="textarea"
        :value="JSON.stringify(modelValue || [], null, 2)"
        :rows="4"
        @update:value="handleJsonUpdate"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { NIcon } from 'naive-ui'

// 添加图标组件
const AddIcon = {
  render() {
    return h('svg', {
      xmlns: 'http://www.w3.org/2000/svg',
      viewBox: '0 0 24 24',
      fill: 'currentColor'
    }, [
      h('path', { d: 'M11 11V5h2v6h6v2h-6v6h-2v-6H5v-2z' })
    ])
  }
}

interface Props {
  itemsSchema?: any
  defs: Record<string, any>
  fieldKey: string
  modelValue?: any[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: any[]]
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

const resolvedItemsSchema = computed(() => {
  return resolveRef(props.itemsSchema, props.defs)
})

const isSimpleStringArray = computed(() => {
  const schema = resolvedItemsSchema.value
  return schema?.type === 'string' && !schema.enum
})

const isSimpleNumberArray = computed(() => {
  const schema = resolvedItemsSchema.value
  return schema?.type === 'number' || schema?.type === 'integer'
})

const hasOneOf = computed(() => {
  return props.itemsSchema?.oneOf
})

const isObjectArray = computed(() => {
  const schema = resolvedItemsSchema.value
  return schema?.type === 'object'
})

// 获取项目标题
function getItemTitle(item: any, index: number): string {
  if (item?.type) {
    return `${item.type} 配置`
  }
  if (item?.name) {
    return item.name
  }
  return `项目 ${index + 1}`
}

// 数组操作
function removeItem(index: number) {
  const newArray = [...(props.modelValue || [])]
  newArray.splice(index, 1)
  emit('update:modelValue', newArray)
}

function updateItem(index: number, value: any) {
  const newArray = [...(props.modelValue || [])]
  newArray[index] = value
  emit('update:modelValue', newArray)
}

function addObjectItem() {
  const newArray = [...(props.modelValue || []), {}]
  emit('update:modelValue', newArray)
}

// oneOf 添加选项
const addOptions = computed(() => {
  if (!props.itemsSchema?.oneOf) return []
  
  return props.itemsSchema.oneOf.map((opt: any, index: number) => {
    const resolved = resolveRef(opt, props.defs)
    return {
      label: resolved?.title || `选项 ${index + 1}`,
      key: index
    }
  })
})

function handleAdd(key: number) {
  const schema = resolveRef(props.itemsSchema.oneOf[key], props.defs)
  let newItem: any = {}
  
  // 如果有 type 枚举，设置默认 type
  if (schema?.properties?.type?.enum) {
    newItem.type = schema.properties.type.enum[0]
  }
  
  const newArray = [...(props.modelValue || []), newItem]
  emit('update:modelValue', newArray)
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
.array-field {
  width: 100%;
}
</style>
