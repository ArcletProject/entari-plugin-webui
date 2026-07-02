<template>
  <el-card class="meta-card" v-if="schema">
    <template #header>元数据设置</template>
    <SchemaForm v-if="patchedSchema" :schema="patchedSchema" v-model="model" />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import SchemaForm from "@/components/schema-form/SchemaForm.vue";

const props = defineProps<{ schema: any; modelValue: any }>();
const emit = defineEmits<{ "update:modelValue": [value: any] }>();
const { t } = useI18n();

const patchedSchema = computed(() => {
  if (!props.schema) return null;
  const properties: Record<string, any> = {};
  for (const [key, prop] of Object.entries<any>(props.schema.properties || {})) {
    const label = t(`meta.${key}`);
    properties[key] = label && !label.startsWith("meta.") ? { ...prop, title: label } : { ...prop };
  }
  return { ...props.schema, properties };
});

const model = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});
</script>

<style scoped>
.meta-card {
  margin-bottom: 16px;
  background: var(--el-fill-color-light);
}
</style>
