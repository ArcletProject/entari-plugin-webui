<template>
  <div class="obj-field">
    <template v-if="objectSchema.properties">
      <SchemaField v-for="(p, k) in objectSchema.properties" :key="k" :field-schema="p" :defs="defs" :field-key="String(k)" :required="objectSchema.required?.includes(String(k))" v-model="model[k]" />
      <AdditionalPropertiesEditor v-if="objectSchema.additionalProperties" :excluded-keys="Object.keys(objectSchema.properties)" :value-schema="typeof objectSchema.additionalProperties==='object'?objectSchema.additionalProperties:{}" :defs="defs" v-model="model" />
    </template>
    <AdditionalPropertiesEditor v-else-if="objectSchema.additionalProperties" :value-schema="typeof objectSchema.additionalProperties==='object'?objectSchema.additionalProperties:{}" :defs="defs" v-model="model" />
    <el-input v-else v-model="jsonText" type="textarea" :rows="4" />
  </div>
</template>
<script setup lang="ts">
import { computed, ref } from "vue";
import SchemaField from "./SchemaField.vue";
import AdditionalPropertiesEditor from "./AdditionalPropertiesEditor.vue";
const props = defineProps<{ objectSchema: any; defs?: any; fieldKey: string; modelValue?: any }>();
const emit = defineEmits<{ "update:modelValue": [v: any] }>();
const model = computed({ get: () => props.modelValue ?? {}, set: (v) => emit("update:modelValue", v) });
const jsonText = ref(JSON.stringify(props.modelValue ?? {}, null, 2));
</script>
