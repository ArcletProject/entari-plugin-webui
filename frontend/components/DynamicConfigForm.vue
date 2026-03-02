<template>
  <div class="dynamic-config-form">
    <template v-if="schema && schema.properties">
      <n-form-item
        v-for="(propSchema, key) in schema.properties"
        :key="key"
        :label="getLabel(propSchema, key)"
      >
        <template #label>
          <n-space align="center" :size="4">
            <span>{{ getLabel(propSchema, key) }}</span>
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

        <!-- 渲染解析后的属性 -->
        <SchemaField
          v-model="model[key]"
          :field-schema="propSchema"
          :defs="schema.$defs || {}"
          :field-key="String(key)"
        />
      </n-form-item>
    </template>

    <!-- additionalProperties 动态键值对 -->
    <template v-if="schema && schema.additionalProperties && !schema.properties">
      <AdditionalPropertiesEditor
        v-model="model"
        :value-schema="schema.additionalProperties"
        :defs="schema.$defs || {}"
      />
    </template>

    <!-- 无 schema 时显示原始 JSON -->
    <template v-else-if="!schema && model && Object.keys(model).length > 0">
      <n-form-item
        v-for="(value, key) in model"
        :key="key"
        :label="String(key)"
      >
        <template v-if="typeof value === 'boolean'">
          <n-switch v-model:value="model[key]" />
        </template>
        <template v-else-if="typeof value === 'number'">
          <n-input-number v-model:value="model[key]" />
        </template>
        <template v-else-if="Array.isArray(value)">
          <n-dynamic-input v-model:value="model[key]" />
        </template>
        <template v-else-if="typeof value === 'object' && value !== null">
          <n-input
            :value="JSON.stringify(value)"
            type="textarea"
            :rows="3"
            @update:value="(v: string) => { try { model[key] = JSON.parse(v) } catch {} }"
          />
        </template>
        <template v-else>
          <n-input v-model:value="model[key]" />
        </template>
      </n-form-item>
    </template>

    <n-empty v-else-if="!schema || !schema.properties" description="暂无配置项" />
  </div>
</template>

<script setup lang="ts">
interface Props {
  schema?: {
    type?: string
    properties?: Record<string, any>
    additionalProperties?: any
    $defs?: Record<string, any>
  }
}

defineProps<Props>()

const model = defineModel<Record<string, any>>({ default: () => ({}) })

function getLabel(propSchema: any, key: string | number): string {
  return propSchema.title || String(key)
}
</script>

<style scoped>
.dynamic-config-form {
  width: 100%;
}

.dynamic-config-form :deep(.n-form-item) {
  margin-bottom: 16px;
}
</style>
