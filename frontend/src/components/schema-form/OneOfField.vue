<template>
  <div class="oneof-field">
    <div
      v-if="isSimple"
      class="simple-row"
    >
      <el-select
        v-model="selectedIndex"
        class="type-select"
        @change="onTypeChange"
      >
        <el-option
          v-for="(o, i) in simpleOptions"
          :key="i"
          :label="labelOf(o)"
          :value="i"
        />
      </el-select>
      <el-input
        v-if="curType==='string'"
        v-model="model"
        class="value-input"
      />
      <el-input-number
        v-else-if="curType==='number'||curType==='integer'"
        v-model="model"
        :step="curType==='integer'?1:0.1"
        class="value-input"
      />
      <el-switch
        v-else-if="curType==='boolean'"
        v-model="model"
      />
      <el-input
        v-else-if="curType==='null'"
        model-value="null"
        disabled
        class="value-input"
      />
    </div>
    <div v-else>
      <el-select
        v-model="selectedIndex"
        style="width:100%;margin-bottom:8px"
        @change="onTypeChange"
      >
        <el-option
          v-for="(o, i) in complexOptions"
          :key="i"
          :label="optionLabel(o, i)"
          :value="i"
        />
      </el-select>
      <el-card v-if="complexOptions[selectedIndex]">
        <SchemaField
          v-model="model"
          :field-schema="complexOptions[selectedIndex]"
          :defs="defs"
          :field-key="fieldKey"
        />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import SchemaField from "./SchemaField.vue";

const props = defineProps<{ oneOf: Record<string, unknown>[]; defs?: Record<string, unknown>; fieldKey: string; modelValue?: unknown }>();
const emit = defineEmits<{ "update:modelValue": [v: unknown] }>();

const simpleTypes = ["string", "number", "integer", "boolean", "null"];
const simpleOptions = computed(() => props.oneOf.filter(o => simpleTypes.includes(o.type as string)));
const complexOptions = computed(() => props.oneOf.filter(o => !simpleTypes.includes(o.type as string)));
const isSimple = computed(() => props.oneOf.every(o => simpleTypes.includes(o.type as string)));
const selectedIndex = ref(0);
const curType = computed(() => simpleOptions.value[selectedIndex.value]?.type);
const model = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});

function labelOf(o: Record<string, unknown>) {
  return o.title || (o.type === "null" ? "空" : o.type);
}
function optionLabel(o: Record<string, unknown>, i: number) {
  const props = o.properties as Record<string, unknown> | undefined;
  const typeSchema = props?.type as Record<string, unknown> | undefined;
  const enumVal = (typeSchema?.enum as unknown[])?.[0] as string;
  return (o.title as string) || enumVal || `选项 ${i + 1}`;
}
function defaultForType(t?: string) {
  if (t === "null") return null;
  if (t === "string") return "";
  if (t === "boolean") return false;
  if (t === "integer" || t === "number") return 0;
  return {};
}
function onTypeChange() {
  emit("update:modelValue", defaultForType(curType.value as string));
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
    const type = (props.modelValue as Record<string, unknown>)?.type as string;
    const i = complexOptions.value.findIndex(o => {
      const typeSchema = (o.properties as Record<string, unknown>)?.type as Record<string, unknown> | undefined;
      const enum_ = typeSchema?.enum as string[] | undefined;
      return enum_?.includes(type);
    });
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
