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
          v-for="(o, i) in resolvedOptions"
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
          v-for="(o, i) in resolvedOptions"
          :key="i"
          :label="optionLabel(o, i)"
          :value="i"
        />
      </el-select>
      <template v-if="selectedResolvedType && simpleTypes.includes(selectedResolvedType)">
        <el-input
          v-if="selectedResolvedType==='string'"
          v-model="model"
          class="value-input"
        />
        <el-input-number
          v-else-if="selectedResolvedType==='number'||selectedResolvedType==='integer'"
          v-model="model"
          :step="selectedResolvedType==='integer'?1:0.1"
          class="value-input"
        />
        <el-switch
          v-else-if="selectedResolvedType==='boolean'"
          v-model="model"
        />
        <el-input
          v-else-if="selectedResolvedType==='null'"
          model-value="null"
          disabled
          class="value-input"
        />
      </template>
      <el-card v-else-if="resolvedOptions[selectedIndex]">
        <SchemaField
          v-model="model"
          :field-schema="resolvedOptions[selectedIndex]"
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

function resolveRef(schema: Record<string, unknown>): Record<string, unknown> {
  if (!schema || !schema.$ref) return schema;
  const m = (schema.$ref as string).match(/#\/(?:\$defs|definitions)\/([^/]+)$/);
  if (m && props.defs?.[m[1]]) {
    const def = props.defs[m[1]] as Record<string, unknown>;
    return { ...def, title: schema.title ?? def.title };
  }
  return schema;
}

const resolvedOptions = computed(() => props.oneOf.map(resolveRef));

const isSimple = computed(() => resolvedOptions.value.every(o => simpleTypes.includes(o.type as string)));
const selectedIndex = ref(0);

const selectedResolvedType = computed(() => resolvedOptions.value[selectedIndex.value]?.type as string | undefined);
const curType = computed<string | undefined>(() => {
  if (isSimple.value) {
    return resolvedOptions.value[selectedIndex.value]?.type as string | undefined;
  }
  return selectedResolvedType.value && simpleTypes.includes(selectedResolvedType.value) ? selectedResolvedType.value : undefined;
});

const model = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});

function labelOf(o: Record<string, unknown>) {
  return o.title || (o.type === "null" ? "空" : (o.type as string));
}

function optionLabel(o: Record<string, unknown>, i: number) {
  const t = o.type as string;
  if (t && simpleTypes.includes(t)) {
    return o.title || (t === "null" ? "空" : t);
  }
  const p = o.properties as Record<string, unknown> | undefined;
  const typeSchema = p?.type as Record<string, unknown> | undefined;
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
  const t = curType.value || "object";
  emit("update:modelValue", defaultForType(t));
}

watch(() => props.modelValue, () => {
  const v = props.modelValue;
  if (v === undefined) return;
  const vType = v === null ? "null" : typeof v;
  const i = resolvedOptions.value.findIndex(o => {
    const oType = o.type as string;
    if (simpleTypes.includes(oType)) {
      const normalized = vType === "number" && Number.isInteger(v) ? "integer" : vType;
      return oType === normalized;
    }
    if (oType === "array" && Array.isArray(v)) return true;
    if (vType === "object" && (oType === "object" || !oType) && !Array.isArray(v)) {
      const typeVal = (v as Record<string, unknown>)?.type as string;
      if (typeVal) {
        const typeSchema = (o.properties as Record<string, unknown>)?.type as Record<string, unknown> | undefined;
        const enum_ = typeSchema?.enum as string[] | undefined;
        if (enum_?.includes(typeVal)) return true;
      }
      return true;
    }
    return false;
  });
  if (i >= 0) selectedIndex.value = i;
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
