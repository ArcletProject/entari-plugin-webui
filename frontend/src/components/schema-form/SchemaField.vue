<template>
  <div class="schema-field">
    <div class="field-header">
      <div class="field-title-row">
        <label class="field-label">
          {{ displayTitle }}
          <span
            v-if="required"
            class="required"
          >*</span>
        </label>
        <div class="field-actions">
          <el-dropdown
            trigger="click"
            @command="onCmd"
          >
            <el-icon
              size="14"
              class="more"
            >
              <MoreFilled />
            </el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="json">
                  编辑 JSON
                </el-dropdown-item>
                <el-dropdown-item command="reset">
                  恢复默认值
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      <div
        v-if="resolved.description"
        class="field-desc"
      >
        {{ resolved.description }}
      </div>
    </div>

    <div class="field-control">
      <!-- const -->
      <el-input
        v-if="resolved.const !== undefined"
        :model-value="String(resolved.const)"
        disabled
      />
      <!-- readOnly -->
      <el-input
        v-else-if="resolved.readOnly"
        :model-value="String(modelValue ?? '')"
        disabled
      />
      <!-- enum -->
      <el-select
        v-else-if="enumOptions"
        v-model="model"
        style="width:100%"
      >
        <el-option
          v-for="o in enumOptions"
          :key="String(o)"
          :label="String(o)"
          :value="o"
        />
      </el-select>
      <!-- boolean -->
      <el-switch
        v-else-if="resolved.type === 'boolean'"
        v-model="model"
      />
      <!-- integer -->
      <el-input-number
        v-else-if="resolved.type === 'integer'"
        v-model="model"
        :step="1"
        style="width:100%"
      />
      <!-- number -->
      <el-input-number
        v-else-if="resolved.type === 'number'"
        v-model="model"
        :step="0.1"
        style="width:100%"
      />
      <!-- array -->
      <ArrayField
        v-else-if="resolved.type === 'array'"
        :model-value="castArray(model)"
        :items-schema="castItemsSchema(resolved.items)"
        :defs="defs"
        :field-key="fieldKey"
        @update:model-value="model = $event"
      />
      <!-- object -->
      <ObjectField
        v-else-if="resolved.type === 'object'"
        v-model="model"
        :object-schema="resolved"
        :defs="defs"
        :field-key="fieldKey"
      />
      <!-- oneOf -->
      <OneOfField
        v-else-if="resolved.oneOf"
        v-model="model"
        :one-of="castSchemas(resolved.oneOf)"
        :defs="defs"
        :field-key="fieldKey"
      />
      <!-- anyOf -->
      <OneOfField
        v-else-if="resolved.anyOf"
        v-model="model"
        :one-of="castSchemas(resolved.anyOf)"
        :defs="defs"
        :field-key="fieldKey"
      />
      <!-- date -->
      <el-date-picker
        v-else-if="resolved.format === 'date'"
        v-model="model"
        type="date"
        style="width:100%"
      />
      <!-- date-time -->
      <el-date-picker
        v-else-if="resolved.format === 'date-time'"
        v-model="model"
        type="datetime"
        style="width:100%"
      />
      <!-- password -->
      <el-input
        v-else-if="resolved.format === 'password'"
        v-model="model"
        type="password"
        show-password
      />
      <!-- textarea for long strings -->
      <el-input
        v-else-if="resolved.format === 'textarea' || castNumber(resolved.maxLength) > 200"
        v-model="model"
        type="textarea"
        :rows="4"
        :placeholder="placeholder"
      />
      <!-- string fallback -->
      <el-input
        v-else
        v-model="model"
        :placeholder="placeholder"
        :type="inputType"
      />
    </div>

    <el-dialog
      v-model="jsonEditing"
      title="编辑 JSON"
      width="500"
    >
      <el-input
        v-model="jsonText"
        type="textarea"
        :rows="10"
      />
      <template #footer>
        <el-button @click="jsonEditing = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="applyJson"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { MoreFilled } from "@element-plus/icons-vue";
import ArrayField from "./ArrayField.vue";
import ObjectField from "./ObjectField.vue";
import OneOfField from "./OneOfField.vue";

const props = defineProps<{
  fieldSchema: Record<string, unknown>;
  defs?: Record<string, unknown>;
  fieldKey: string;
  required?: boolean;
  modelValue?: unknown;
}>();
const emit = defineEmits<{ "update:modelValue": [v: unknown] }>();

const resolved = computed(() => resolveRef(props.fieldSchema, props.defs));
const displayTitle = computed(() => resolved.value.title || props.fieldKey);
const placeholder = computed(() => {
  if (resolved.value.default != null) return String(resolved.value.default);
  return undefined;
});
const inputType = computed(() => {
  const fmt = resolved.value.format;
  if (fmt === "email") return "email";
  if (fmt === "uri" || fmt === "url") return "url";
  if (fmt === "tel") return "tel";
  return "text";
});

const model = computed({
  get: () => props.modelValue ?? defaultFor(resolved.value),
  set: (v) => emit("update:modelValue", v),
});

const enumOptions = computed(() => {
  if (Array.isArray(resolved.value.enum)) return resolved.value.enum;
  if (Array.isArray(resolved.value.oneOf)) {
    const primitive = resolved.value.oneOf.filter((o: Record<string, unknown>) => o.const !== undefined);
    if (primitive.length) return primitive.map((o: Record<string, unknown>) => o.const);
  }
  return null;
});

function resolveRef(schema: Record<string, unknown>, defs?: Record<string, unknown>): Record<string, unknown> {
  if (!schema) return {};
  if (!schema.$ref && !schema.oneOf && !schema.anyOf && !schema.$defs) return schema;
  if (schema.$ref) {
    const m = (schema.$ref as string).match(/#\/(?:\$defs|definitions)\/([^/]+)$/);
    if (m && defs?.[m[1]]) {
      const def = defs[m[1]] as Record<string, unknown>;
      return {
        ...def,
        description: schema.description ?? def.description,
        title: schema.title ?? def.title,
      };
    }
  }
  return schema;
}

function castArray(v: unknown): unknown[] { return v as unknown[] }
function castItemsSchema(v: unknown): Record<string, unknown> | undefined { return v as Record<string, unknown> | undefined }
function castSchemas(v: unknown): Record<string, unknown>[] { return v as Record<string, unknown>[] }
function castNumber(v: unknown): number { return v as number }

function defaultFor(schema: Record<string, unknown>): unknown {
  if (schema.default !== undefined) return schema.default;
  if (schema.const !== undefined) return schema.const;
  switch (schema.type) {
    case "boolean": return false;
    case "integer": return 0;
    case "number": return 0;
    case "string": return "";
    case "array": return [];
    case "object": return {};
    default: return null;
  }
}

const jsonEditing = ref(false);
const jsonText = ref("");
function onCmd(cmd: string) {
  if (cmd === "json") {
    jsonText.value = JSON.stringify(props.modelValue ?? null, null, 2);
    jsonEditing.value = true;
  }
  if (cmd === "reset") {
    emit("update:modelValue", defaultFor(resolved.value));
  }
}
function applyJson() {
  try {
    emit("update:modelValue", JSON.parse(jsonText.value));
    jsonEditing.value = false;
  } catch {
    // ignore invalid
  }
}
</script>

<style scoped>
.schema-field {
  margin-bottom: 16px;
}
.field-header {
  margin-bottom: 6px;
}
.field-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.field-label {
  font-weight: 500;
  color: var(--el-text-color-regular);
}
.required {
  color: var(--el-color-danger);
  margin-left: 2px;
}
.field-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
  line-height: 1.4;
}
.field-actions {
  margin-left: auto;
}
.more {
  cursor: pointer;
  color: var(--el-text-color-secondary);
}
.field-control {
  width: 100%;
}
</style>
