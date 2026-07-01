<template><div class="field">
  <label class="field-label">{{ fieldSchema.title || fieldKey }}
    <span v-if="required" style="color:var(--el-color-danger)">*</span>
  </label>
  <el-tooltip v-if="fieldSchema.description" :content="fieldSchema.description" placement="top"><el-icon><InfoFilled /></el-icon></el-tooltip>

  <!-- readOnly -->
  <el-input v-if="resolved.readOnly" :model-value="String(modelValue ?? '')" disabled />
  <!-- enum -->
  <el-select v-else-if="enumOptions" v-model="model">
    <el-option v-for="o in enumOptions" :key="o" :label="o" :value="o" />
  </el-select>
  <!-- boolean -->
  <el-switch v-else-if="resolved.type === 'boolean'" v-model="model" />
  <!-- number/integer -->
  <el-input-number v-else-if="resolved.type === 'integer' || resolved.type === 'number'" v-model="model" :step="resolved.type === 'integer' ? 1 : 0.1" />
  <!-- array -->
  <ArrayField v-else-if="resolved.type === 'array'" :items-schema="resolved.items" :defs="defs" :field-key="fieldKey" v-model="model" />
  <!-- object -->
  <ObjectField v-else-if="resolved.type === 'object'" :object-schema="resolved" :defs="defs" :field-key="fieldKey" v-model="model" />
  <!-- oneOf -->
  <OneOfField v-else-if="resolved.oneOf" :one-of="resolved.oneOf" :defs="defs" :field-key="fieldKey" v-model="model" />
  <!-- password -->
  <el-input v-else-if="resolved.format === 'password'" v-model="model" type="password" show-password />
  <!-- string -->
  <el-input v-else v-model="model" :placeholder="resolved.default != null ? String(resolved.default) : ''" />

  <el-dropdown trigger="click" @command="onCmd">
    <el-icon><MoreFilled /></el-icon>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="json">编辑 JSON</el-dropdown-item>
        <el-dropdown-item command="reset">恢复默认值</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>

  <el-dialog v-model="jsonEditing" title="编辑 JSON" width="500">
    <el-input v-model="jsonText" type="textarea" :rows="10" />
    <template #footer><el-button @click="jsonEditing=false">取消</el-button><el-button type="primary" @click="applyJson">确定</el-button></template>
  </el-dialog>
</div>
</template>
<script setup lang="ts">
import { computed, ref } from "vue";
import { InfoFilled, MoreFilled } from "@element-plus/icons-vue";
import ArrayField from "./ArrayField.vue";
import ObjectField from "./ObjectField.vue";
import OneOfField from "./OneOfField.vue";

const props = defineProps<{ fieldSchema: any; defs?: any; fieldKey: string; required?: boolean; modelValue?: any }>();
const emit = defineEmits<{ "update:modelValue": [v: any] }>();

const resolved = computed(() => resolveRef(props.fieldSchema, props.defs));

const model = computed({
  get: () => props.modelValue ?? defaultFor(resolved.value),
  set: (v) => emit("update:modelValue", v),
});

const enumOptions = computed(() =>
  Array.isArray(resolved.value.enum) ? resolved.value.enum : (
    resolved.value.type === "string" && resolved.value.oneOf ? null : null));

function resolveRef(schema: any, defs: any): any {
  if (!schema?.$ref && !schema?.oneOf && !schema?.$defs) return schema;
  if (schema.$ref) {
    const m = schema.$ref.match(/\$defs\/([^/]+)$/);
    if (m && defs?.[m[1]]) {
      const r = { ...defs[m[1]], description: schema.description ?? defs[m[1]].description, title: schema.title ?? defs[m[1]].title };
      return r;
    }
  }
  return schema;
}

function defaultFor(schema: any): any {
  if (schema.default !== undefined) return schema.default;
  switch (schema.type) {
    case "boolean": return false;
    case "integer": case "number": return 0;
    case "string": return "";
    case "array": return [];
    case "object": return {};
    default: return null;
  }
}

const jsonEditing = ref(false);
const jsonText = ref("");
function onCmd(cmd: string) {
  if (cmd === "json") { jsonText.value = JSON.stringify(props.modelValue ?? null, null, 2); jsonEditing.value = true; }
  if (cmd === "reset") { emit("update:modelValue", defaultFor(resolved.value)); }
}
function applyJson() {
  try { emit("update:modelValue", JSON.parse(jsonText.value)); jsonEditing.value = false; }
  catch { /* ignore invalid */ }
}
</script>
