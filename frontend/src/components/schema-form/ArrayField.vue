<template>
  <div class="array-field">
    <!-- 简单字符串/数字数组 -->
    <div
      v-if="isPrimitiveItems"
      class="primitive-array"
    >
      <el-tag
        v-for="(item, i) in model"
        :key="i"
        closable
        style="margin-right: 8px; margin-bottom: 8px"
        @close="remove(i)"
      >
        {{ item }}
      </el-tag>
      <div class="add-row">
        <el-input
          v-model="newValue"
          :placeholder="`添加 ${itemType}`"
          style="width: 180px"
          @keyup.enter="addPrimitive"
        />
        <el-button @click="addPrimitive">
          添加
        </el-button>
      </div>
    </div>
    <!-- 对象数组 -->
    <div v-else-if="isObjectItems">
      <el-card
        v-for="(_, i) in model"
        :key="i"
        style="margin-bottom: 8px"
      >
        <template #header>
          <div class="card-header">
            <span>项目 {{ i + 1 }}</span>
            <el-button
              text
              type="danger"
              size="small"
              @click="remove(i)"
            >
              删除
            </el-button>
          </div>
        </template>
        <ObjectField
          v-model="model[i]"
          :object-schema="itemsSchema"
          :defs="defs"
          :field-key="`${fieldKey}[${i}]`"
        />
      </el-card>
      <el-button @click="addObject">
        添加项目
      </el-button>
    </div>
    <!-- oneOf/anyOf 数组 -->
    <div v-else-if="isUnionItems">
      <el-card
        v-for="(_, i) in model"
        :key="i"
        style="margin-bottom: 8px"
      >
        <template #header>
          <div class="card-header">
            <span>项目 {{ i + 1 }}</span>
            <el-button
              text
              type="danger"
              size="small"
              @click="remove(i)"
            >
              删除
            </el-button>
          </div>
        </template>
        <OneOfField
          v-model="model[i]"
          :one-of="resolvedOneOf"
          :defs="defs"
          :field-key="`${fieldKey}[${i}]`"
        />
      </el-card>
      <el-button @click="addUnion">
        添加项目
      </el-button>
    </div>
    <!-- fallback -->
    <el-input
      v-else
      v-model="jsonText"
      type="textarea"
      :rows="4"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import ObjectField from "./ObjectField.vue";
import OneOfField from "./OneOfField.vue";

const props = defineProps<{ itemsSchema?: Record<string, unknown>; defs?: Record<string, unknown>; fieldKey: string; modelValue?: unknown[] }>();
const emit = defineEmits<{ "update:modelValue": [v: unknown[]] }>();

const model = computed<unknown[]>({
  get: () => props.modelValue ?? [],
  set: (v) => emit("update:modelValue", v),
});

const itemType = computed(() => props.itemsSchema?.type);
const isPrimitiveItems = computed(() => ["string", "number", "integer"].includes(itemType.value));
const isObjectItems = computed(() => itemType.value === "object");
const isUnionItems = computed(() => !!(props.itemsSchema?.oneOf || props.itemsSchema?.anyOf));
const resolvedOneOf = computed(() => (props.itemsSchema?.oneOf || props.itemsSchema?.anyOf || []).map((o: Record<string, unknown>) => resolveRef(o, props.defs)));

const jsonText = ref(JSON.stringify(props.modelValue ?? [], null, 2));
const newValue = ref("");

function remove(i: number) {
  const next = model.value.slice();
  next.splice(i, 1);
  emit("update:modelValue", next);
}
function addPrimitive() {
  if (newValue.value === "") return;
  const val = itemType.value === "integer" ? parseInt(newValue.value, 10) : itemType.value === "number" ? parseFloat(newValue.value) : newValue.value;
  emit("update:modelValue", [...model.value, val]);
  newValue.value = "";
}
function addObject() {
  emit("update:modelValue", [...model.value, {}]);
}
function addUnion() {
  const first = resolvedOneOf.value[0];
  if (!first) {
    emit("update:modelValue", [...model.value, {}]);
    return;
  }
  const type = first.properties?.type?.enum?.[0];
  emit("update:modelValue", [...model.value, type !== undefined ? { type } : defaultForSchema(first)]);
}

function resolveRef(schema: Record<string, unknown>, defs?: Record<string, unknown>): Record<string, unknown> {
  if (!schema) return {};
  if (schema.$ref) {
    const m = schema.$ref.match(/#\/(?:\$defs|definitions)\/([^/]+)$/);
    if (m && defs?.[m[1]]) {
      return {
        ...defs[m[1]],
        description: schema.description ?? defs[m[1]].description,
        title: schema.title ?? defs[m[1]].title,
      };
    }
  }
  return schema;
}

function defaultForSchema(schema: Record<string, unknown>): unknown {
  if (schema.default !== undefined) return schema.default;
  if (schema.const !== undefined) return schema.const;
  if (schema.type === "object") {
    const out: Record<string, unknown> = {};
    const props = (schema.properties ?? {}) as Record<string, Record<string, unknown>>;
    for (const [k, v] of Object.entries(props)) {
      out[k] = v.default !== undefined ? v.default : defaultForSchema(v);
    }
    return out;
  }
  switch (schema.type) {
    case "boolean": return false;
    case "integer": return 0;
    case "number": return 0;
    case "string": return "";
    case "array": return [];
    default: return null;
  }
}
</script>

<style scoped>
.array-field {
  width: 100%;
}
.primitive-array {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.add-row {
  display: flex;
  gap: 8px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
