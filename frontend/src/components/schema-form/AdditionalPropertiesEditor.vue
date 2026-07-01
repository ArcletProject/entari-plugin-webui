<template><div class="ap-editor">
  <el-divider v-if="excludedKeys?.length" content-position="left">附加属性</el-divider>
  <el-card v-for="(v, k) in extra" :key="k" closable @close="delete (model as any)[k]" style="margin-bottom:8px">
    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
      <el-input v-model="renameMap[String(k)]" placeholder="属性名" style="width:180px" @blur="rename(String(k), renameMap[String(k)])" />
    </div>
    <SchemaField v-if="valueSchema && Object.keys(valueSchema).length" :field-schema="valueSchema" :defs="defs" :field-key="String(k)" v-model="model[String(k)]" />
    <el-input v-else v-model="model[String(k)]" />
  </el-card>
  <div style="display:flex;gap:8px">
    <el-input v-model="newKey" placeholder="新属性名" />
    <el-button @click="add">添加属性</el-button>
  </div>
</div></template>
<script setup lang="ts">
import { computed, ref, watch } from "vue";
import SchemaField from "./SchemaField.vue";
const props = defineProps<{ valueSchema?: any; defs?: any; excludedKeys?: string[]; modelValue?: Record<string, any> }>();
const emit = defineEmits<{ "update:modelValue": [v: Record<string, any>] }>();
const excluded = computed(() => props.excludedKeys ?? []);
const model = computed<Record<string, any>>({ get: () => props.modelValue ?? {}, set: (v) => emit("update:modelValue", v) });
const extra = computed(() => Object.fromEntries(Object.entries(model.value).filter(([k]) => !excluded.value.includes(k))));
const renameMap = ref<Record<string, string>>({});
const newKey = ref("");

watch(extra, (val) => {
  renameMap.value = Object.fromEntries(Object.keys(val).map(k => [k, k]));
}, { immediate: true });

function add() {
  if (!newKey.value) return;
  const type = props.valueSchema?.type;
  model.value[newKey.value] = type === "boolean" ? false : type === "object" ? {} : type === "array" ? [] : "";
  newKey.value = "";
}
function rename(oldKey: string, newKey: string) {
  if (!newKey || newKey === oldKey) return;
  const next = { ...model.value };
  next[newKey] = next[oldKey];
  delete next[oldKey];
  emit("update:modelValue", next);
}
</script>
