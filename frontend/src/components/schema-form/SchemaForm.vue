<template>
  <div class="schema-form">
    <template v-if="schema?.properties">
      <SchemaField
        v-for="(prop, key) in schema.properties"
        :key="key"
        :field-schema="prop"
        :defs="resolvedDefs"
        :field-key="String(key)"
        :required="schema.required?.includes(String(key))"
        v-model="model[key]"
      />
    </template>
    <ObjectField
      v-else-if="schema?.type === 'object'"
      :object-schema="schema"
      :defs="resolvedDefs"
      field-key="root"
      v-model="model"
    />
    <AdditionalPropertiesEditor
      v-else-if="schema?.additionalProperties"
      :value-schema="typeof schema.additionalProperties === 'object' ? schema.additionalProperties : {}"
      :defs="resolvedDefs"
      v-model="model"
    />
    <el-empty v-else description="无配置项" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import SchemaField from "./SchemaField.vue";
import ObjectField from "./ObjectField.vue";
import AdditionalPropertiesEditor from "./AdditionalPropertiesEditor.vue";

// modelValue: record<string, any>; schema: JSON Schema object
const props = defineProps<{ schema?: any; modelValue?: Record<string, any> }>();
const emit = defineEmits<{ "update:modelValue": [v: Record<string, any>] }>();

const resolvedDefs = computed(() => props.schema?.$defs || props.schema?.$defs || {});
const model = ref<Record<string, any>>({ ...(props.modelValue ?? {}) });

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
