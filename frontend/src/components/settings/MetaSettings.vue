<template>
  <el-card class="meta-card" v-if="schema">
    <template #header>元数据设置</template>
    <SchemaForm v-if="schema" :schema="schema" v-model="model" />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SchemaForm from "@/components/schema-form/SchemaForm.vue";

const props = defineProps<{ schema: any; modelValue: any }>();
const emit = defineEmits<["update:modelValue"]>();

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
