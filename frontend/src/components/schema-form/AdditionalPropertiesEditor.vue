<template>
  <div class="ap-editor">
    <el-divider
      v-if="excludedKeys?.length"
      content-position="left"
    >
      附加属性
    </el-divider>
    <el-card
      v-for="(v, k) in extra"
      :key="String(k)"
      style="margin-bottom: 8px"
    >
      <template #header>
        <div class="card-header">
          <el-input
            v-model="renameMap[String(k)]"
            placeholder="属性名"
            style="width: 180px"
            size="small"
            @blur="rename(String(k), renameMap[String(k)])"
          />
          <el-button
            text
            type="danger"
            size="small"
            @click="remove(String(k))"
          >
            删除
          </el-button>
        </div>
      </template>
      <SchemaField
        v-if="hasValueSchema"
        v-model="model[String(k)]"
        :field-schema="valueSchema!"
        :defs="defs"
        :field-key="String(k)"
      />
      <el-input
        v-else
        v-model="model[String(k)]"
      />
    </el-card>
    <div class="add-row">
      <el-input
        v-model="newKey"
        placeholder="新属性名"
      />
      <el-button @click="add">
        添加属性
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import SchemaField from "./SchemaField.vue";

const props = defineProps<{
  valueSchema?: Record<string, unknown>;
  defs?: Record<string, unknown>;
  excludedKeys?: string[];
  modelValue?: Record<string, unknown>;
}>();
const emit = defineEmits<{ "update:modelValue": [v: Record<string, unknown>] }>();

const excluded = computed(() => props.excludedKeys ?? []);
const model = computed<Record<string, unknown>>({
  get: () => props.modelValue ?? {},
  set: (v) => emit("update:modelValue", v),
});
const extra = computed(() =>
  Object.fromEntries(Object.entries(model.value).filter(([k]) => !excluded.value.includes(k)))
);
const hasValueSchema = computed(() => props.valueSchema && Object.keys(props.valueSchema).length > 0);

function resolveRef(schema: Record<string, unknown>, defs?: Record<string, unknown>): Record<string, unknown> {
  if (!schema || !schema.$ref) return schema;
  const m = (schema.$ref as string).match(/#\/(?:\$defs|definitions)\/([^/]+)$/);
  if (m && defs?.[m[1]]) {
    const def = defs[m[1]] as Record<string, unknown>;
    return { ...def, description: schema.description ?? def.description, title: schema.title ?? def.title };
  }
  return schema;
}

const renameMap = ref<Record<string, string>>({});
const newKey = ref("");

watch(extra, (val) => {
  renameMap.value = Object.fromEntries(Object.keys(val).map(k => [k, k]));
}, { immediate: true });

function add() {
  if (!newKey.value) return;
  const vs = resolveRef(props.valueSchema ?? {}, props.defs);
  const type = vs.type;
  const defaultValue = type === "boolean" ? false : type === "object" ? {} : type === "array" ? [] : "";
  model.value[newKey.value] = defaultValue;
  newKey.value = "";
}
function remove(k: string) {
  const next = { ...model.value };
  delete next[k];
  emit("update:modelValue", next);
}
function rename(oldKey: string, newKeyName: string) {
  if (!newKeyName || newKeyName === oldKey) return;
  const next = { ...model.value };
  next[newKeyName] = next[oldKey];
  delete next[oldKey];
  emit("update:modelValue", next);
}
</script>

<style scoped>
.ap-editor {
  width: 100%;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.add-row {
  display: flex;
  gap: 8px;
}
</style>
