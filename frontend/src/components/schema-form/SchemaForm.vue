<template>
  <div class="schema-form">
    <template v-if="schema?.properties">
      <SchemaField
        v-for="(prop, key) in (schema.properties as Record<string, unknown>)"
        :key="key"
        v-model="model[key]"
        :field-schema="prop as Record<string, unknown>"
        :defs="resolvedDefs"
        :field-key="String(key)"
        :required="(schema.required as string[])?.includes(String(key))"
      />
    </template>
    <ObjectField
      v-else-if="schema?.type === 'object'"
      v-model="model"
      :object-schema="schema!"
      :defs="resolvedDefs"
      field-key="root"
    />
    <AdditionalPropertiesEditor
      v-else-if="schema?.additionalProperties"
      v-model="model"
      :value-schema="typeof schema.additionalProperties === 'object' ? (schema.additionalProperties as Record<string, unknown>) : {}"
      :defs="resolvedDefs"
    />
    <el-empty
      v-else
      description="无配置项"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import SchemaField from "./SchemaField.vue";
import ObjectField from "./ObjectField.vue";
import AdditionalPropertiesEditor from "./AdditionalPropertiesEditor.vue";

// modelValue: record<string, any>; schema: JSON Schema object
const props = defineProps<{ schema?: Record<string, unknown>; modelValue?: Record<string, unknown> }>();
const emit = defineEmits<{ "update:modelValue": [v: Record<string, unknown>] }>();

const resolvedDefs = computed(() => (props.schema?.$defs || props.schema?.$defs || {}) as Record<string, unknown>);
const model = ref<Record<string, unknown>>({ ...(props.modelValue ?? {}) });

watch(() => props.modelValue, (v) => {
  const next = v ?? {};
  // 仅在内容真正变化时同步，避免与 v-model 形成无限循环
  if (JSON.stringify(next) !== JSON.stringify(model.value)) {
    model.value = { ...next };
  }
}, { deep: true });

watch(model, (v) => emit("update:modelValue", v), { deep: true });
</script>

<style scoped>
.schema-form {
  padding: 8px 0;
}
</style>
