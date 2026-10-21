<template>
  <div class="object-field">
    <template v-if="objectSchema.properties">
      <el-collapse
        v-if="collapsible"
        v-model="activeNames"
      >
        <el-collapse-item
          :title="collapseTitle"
          :name="fieldKey"
        >
          <SchemaField
            v-for="(p, k) in objectSchema.properties"
            :key="k"
            :model-value="model[k]"
            :field-schema="p"
            :root-schema="rootSchema"
            :field-key="String(k)"
            :required="(objectSchema.required as string[])?.includes(String(k))"
            @update:model-value="setKey(String(k), $event)"
          />
          <AdditionalPropertiesEditor
            v-if="objectSchema.additionalProperties"
            v-model="model"
            :excluded-keys="Object.keys(objectSchema.properties!)"
            :value-schema="typeof objectSchema.additionalProperties === 'object' ? (objectSchema.additionalProperties as Record<string, unknown>) : {}"
            :root-schema="rootSchema"
          />
        </el-collapse-item>
      </el-collapse>
      <template v-else>
        <SchemaField
          v-for="(p, k) in objectSchema.properties"
          :key="k"
          :model-value="model[k]"
          :field-schema="p"
          :root-schema="rootSchema"
          :field-key="String(k)"
          :required="(objectSchema.required as string[])?.includes(String(k))"
          @update:model-value="setKey(String(k), $event)"
        />
        <AdditionalPropertiesEditor
          v-if="objectSchema.additionalProperties"
          v-model="model"
          :excluded-keys="Object.keys(objectSchema.properties!)"
          :value-schema="typeof objectSchema.additionalProperties === 'object' ? (objectSchema.additionalProperties as Record<string, unknown>) : {}"
          :root-schema="rootSchema"
        />
      </template>
    </template>
    <AdditionalPropertiesEditor
      v-else-if="objectSchema.additionalProperties"
      v-model="model"
      :value-schema="typeof objectSchema.additionalProperties === 'object' ? (objectSchema.additionalProperties as Record<string, unknown>) : {}"
      :root-schema="rootSchema"
    />
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
import SchemaField from "./SchemaField.vue";
import AdditionalPropertiesEditor from "./AdditionalPropertiesEditor.vue";

const props = defineProps<{ objectSchema: Record<string, unknown>; rootSchema?: Record<string, unknown>; fieldKey: string; modelValue?: unknown }>();
const emit = defineEmits<{ "update:modelValue": [v: unknown] }>();

const model = computed({
  get: () => (props.modelValue ?? {}) as Record<string, unknown>,
  set: (v) => emit("update:modelValue", v),
});

function setKey(key: string, value: unknown) {
  const wasPresent = props.modelValue !== undefined;
  const next = { ...((props.modelValue ?? {}) as Record<string, unknown>) };
  if (value === undefined) delete next[key];
  else next[key] = value;
  // 原本不存在的对象被清空后，回退成 undefined，让父级删除这个 key
  if (!wasPresent && Object.keys(next).length === 0) {
    emit("update:modelValue", undefined);
    return;
  }
  emit("update:modelValue", next);
}
const jsonText = ref(JSON.stringify(props.modelValue ?? {}, null, 2));
const collapsible = computed(() => props.objectSchema.collapsible ?? false);
const collapseTitle = computed(() => props.objectSchema.title || "对象");
const activeNames = ref<string[]>([props.fieldKey]);
</script>

<style scoped>
.object-field {
  width: 100%;
}
</style>
