<template>
  <div class="schema-form">
    <template v-if="schema?.properties">
      <SchemaField v-for="(prop, key) in schema.properties" :key="key" :field-schema="prop" :defs="schema.$defs" :field-key="String(key)" :required="schema.required?.includes(String(key))" v-model="model[key]" />
    </template>
    <AdditionalPropertiesEditor v-else-if="schema?.additionalProperties" :value-schema="typeof schema.additionalProperties === 'object' ? schema.additionalProperties : {}" :defs="schema.$defs" v-model="model" />
    <el-empty v-else-if="!Object.keys(model || {}).length" description="无配置项" />
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from "vue";
import SchemaField from "./SchemaField.vue";
import AdditionalPropertiesEditor from "./AdditionalPropertiesEditor.vue";

// modelValue: record<string, any>; schema: JSON Schema object
const props = defineProps<{ schema?: any; modelValue?: Record<string, any> }>();
const emit = defineEmits<{ "update:modelValue": [v: Record<string, any>] }>();
const model = ref<Record<string, any>>(props.modelValue ?? {});
watch(model, (v) => emit("update:modelValue", v), { deep: true });
</script>
