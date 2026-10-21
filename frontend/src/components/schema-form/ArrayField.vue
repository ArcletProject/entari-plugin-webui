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
          :model-value="model[i]"
          :object-schema="resolvedItemsSchema!"
          @update:model-value="setItem(i, $event)"
          :root-schema="rootSchema"
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
          :model-value="model[i]"
          :one-of="resolvedOneOf"
          @update:model-value="setItem(i, $event)"
          :root-schema="rootSchema"
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
import { resolveRef } from "./resolve-ref";

const props = defineProps<{ itemsSchema?: Record<string, unknown>; rootSchema?: Record<string, unknown>; fieldKey: string; modelValue?: unknown[] }>();
const emit = defineEmits<{ "update:modelValue": [v: unknown[]] }>();

const model = computed<unknown[]>({
  get: () => props.modelValue ?? [],
  set: (v) => emit("update:modelValue", v),
});

const resolvedItemsSchema = computed(() => props.itemsSchema ? resolveRef(props.itemsSchema, props.rootSchema ?? {}) : undefined);
const itemType = computed(() => resolvedItemsSchema.value?.type as string | undefined);
const isPrimitiveItems = computed(() => ["string", "number", "integer"].includes(itemType.value!));
const isObjectItems = computed(() => itemType.value === "object");
const isUnionItems = computed(() => !!((resolvedItemsSchema.value?.oneOf || resolvedItemsSchema.value?.anyOf) as unknown[] | undefined));
const resolvedOneOf = computed(() => {
  const items = (resolvedItemsSchema.value?.oneOf || resolvedItemsSchema.value?.anyOf) as Record<string, unknown>[] | undefined;
  return (items || []).map((o) => resolveRef(o, props.rootSchema ?? {}));
});

const jsonText = ref(JSON.stringify(props.modelValue ?? [], null, 2));
const newValue = ref("");

function remove(i: number) {
  const next = model.value.slice();
  next.splice(i, 1);
  emit("update:modelValue", next);
}
function setItem(i: number, value: unknown) {
  const next = model.value.slice();
  // 数组项被“恢复默认”时保留位置，用空对象代替 undefined
  next[i] = value === undefined ? {} : value;
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
  const props = first.properties as Record<string, unknown> | undefined;
  const type = ((props?.type as Record<string, unknown>)?.enum as unknown[])?.[0] as string;
  // 只写类型判别字段；其余字段留空，由 placeholder 显示默认值
  emit("update:modelValue", [...model.value, type !== undefined ? { type } : {}]);
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
