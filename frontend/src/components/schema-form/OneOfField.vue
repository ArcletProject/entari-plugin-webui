<template>
  <div class="oneof-field">
    <div v-if="isSimple" class="simple-row">
      <el-select v-model="selectedIndex" @change="onTypeChange" class="type-select">
        <el-option v-for="(o, i) in simpleOptions" :key="i" :label="labelOf(o)" :value="i" />
      </el-select>
      <el-input v-if="curType==='string'" v-model="model" class="value-input" />
      <el-input-number v-else-if="curType==='number'||curType==='integer'" v-model="model" :step="curType==='integer'?1:0.1" class="value-input" />
      <el-switch v-else-if="curType==='boolean'" v-model="model" />
      <el-input v-else-if="curType==='null'" model-value="null" disabled class="value-input" />
    </div>
    <div v-else>
      <el-select v-model="selectedIndex" @change="onTypeChange" style="width:100%;margin-bottom:8px">
        <el-option v-for="(o, i) in complexOptions" :key="i" :label="optionLabel(o, i)" :value="i" />
      </el-select>
      <el-card v-if="complexOptions[selectedIndex]">
        <SchemaField :field-schema="complexOptions[selectedIndex]" :defs="defs" :field-key="fieldKey" v-model="model" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import SchemaField from "./SchemaField.vue";

const props = defineProps<{ oneOf: any[]; defs?: any; fieldKey: string; modelValue?: any }>();
const emit = defineEmits<{ "update:modelValue": [v: any] }>();

const simpleTypes = ["string", "number", "integer", "boolean", "null"];
const simpleOptions = computed(() => props.oneOf.filter(o => simpleTypes.includes(o.type)));
const complexOptions = computed(() => props.oneOf.filter(o => !simpleTypes.includes(o.type)));
const isSimple = computed(() => props.oneOf.every(o => simpleTypes.includes(o.type)));
const selectedIndex = ref(0);
const curType = computed(() => simpleOptions.value[selectedIndex.value]?.type);
const model = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});

function labelOf(o: any) {
  return o.title || (o.type === "null" ? "空" : o.type);
}
function optionLabel(o: any, i: number) {
  return o.title || o.properties?.type?.enum?.[0] || `选项 ${i + 1}`;
}
function defaultForType(t?: string) {
  if (t === "null") return null;
  if (t === "string") return "";
  if (t === "boolean") return false;
  if (t === "integer" || t === "number") return 0;
  return {};
}
function onTypeChange() {
  emit("update:modelValue", defaultForType(curType.value));
}

watch(() => props.modelValue, () => {
  if (isSimple.value) {
    const v = props.modelValue;
    const type = v === null ? "null" : typeof v;
    const i = simpleOptions.value.findIndex(o =>
      o.type === (type === "number" && Number.isInteger(v) ? "integer" : type)
    );
    if (i >= 0) selectedIndex.value = i;
  } else {
    const type = props.modelValue?.type;
    const i = complexOptions.value.findIndex(o =>
      o.properties?.type?.enum?.includes(type)
    );
    if (i >= 0) selectedIndex.value = i;
  }
}, { immediate: true });
</script>

<style scoped>
.oneof-field {
  width: 100%;
}
.simple-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.type-select {
  width: 140px;
  flex-shrink: 0;
}
.value-input {
  flex: 1;
  min-width: 0;
}
</style>
