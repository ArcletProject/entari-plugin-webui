<template><div class="oneof-field">
  <div v-if="isSimple">
    <el-select v-model="selectedIndex" @change="onTypeChange">
      <el-option v-for="(o,i) in simpleOptions" :key="i" :label="labelOf(o)" :value="i" />
    </el-select>
    <el-input v-if="curType==='string'" v-model="model" />
    <el-input-number v-else-if="curType==='number'||curType==='integer'" v-model="model" :step="curType==='integer'?1:0.1" />
    <el-switch v-else-if="curType==='boolean'" v-model="model" />
  </div>
  <div v-else>
    <el-select v-model="selectedIndex" @change="onTypeChange">
      <el-option v-for="(o,i) in complexOptions" :key="i" :label="o.title || o.properties?.type?.enum?.[0] || `选项${i+1}`" :value="i" />
    </el-select>
    <el-card style="margin-top:8px">
      <SchemaField :field-schema="complexOptions[selectedIndex]" :defs="defs" :field-key="fieldKey" v-model="model" />
    </el-card>
  </div>
</div></template>
<script setup lang="ts">
import { computed, ref, watch } from "vue";
import SchemaField from "./SchemaField.vue";
const props = defineProps<{ oneOf: any[]; defs?: any; fieldKey: string; modelValue?: any }>();
const emit = defineEmits<{ "update:modelValue": [v: any] }>();
const simpleTypes = ["string","number","integer","boolean","null"];
const simpleOptions = computed(() => props.oneOf.filter(o => simpleTypes.includes(o.type)));
const complexOptions = computed(() => props.oneOf.filter(o => !simpleTypes.includes(o.type)));
const isSimple = computed(() => props.oneOf.every(o => simpleTypes.includes(o.type)));
const selectedIndex = ref(0);
const curType = computed(() => simpleOptions.value[selectedIndex.value]?.type);
const model = computed({ get: () => props.modelValue, set: (v) => emit("update:modelValue", v) });
function labelOf(o:any){return o.type==="null"?"空":o.type;}
function onTypeChange() {
  const t = curType.value;
  emit("update:modelValue", t==="null"?null:t==="string"?"":t==="boolean"?false:0);
}
watch(() => props.modelValue, () => {
  // 由值反推 index（简单类型）
  if (isSimple.value) {
    const v = props.modelValue;
    const i = simpleOptions.value.findIndex(o => o.type === (v===null?"null":typeof v==="string"?"string":typeof v));
    if (i >= 0) selectedIndex.value = i;
  }
}, { immediate: true });
</script>
