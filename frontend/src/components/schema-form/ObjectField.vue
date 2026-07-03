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
            v-model="model[k]"
            :field-schema="p"
            :defs="defs"
            :field-key="String(k)"
            :required="objectSchema.required?.includes(String(k))"
          />
          <AdditionalPropertiesEditor
            v-if="objectSchema.additionalProperties"
            v-model="model"
            :excluded-keys="Object.keys(objectSchema.properties)"
            :value-schema="typeof objectSchema.additionalProperties === 'object' ? objectSchema.additionalProperties : {}"
            :defs="defs"
          />
        </el-collapse-item>
      </el-collapse>
      <template v-else>
        <SchemaField
          v-for="(p, k) in objectSchema.properties"
          :key="k"
          v-model="model[k]"
          :field-schema="p"
          :defs="defs"
          :field-key="String(k)"
          :required="objectSchema.required?.includes(String(k))"
        />
        <AdditionalPropertiesEditor
          v-if="objectSchema.additionalProperties"
          v-model="model"
          :excluded-keys="Object.keys(objectSchema.properties)"
          :value-schema="typeof objectSchema.additionalProperties === 'object' ? objectSchema.additionalProperties : {}"
          :defs="defs"
        />
      </template>
    </template>
    <AdditionalPropertiesEditor
      v-else-if="objectSchema.additionalProperties"
      v-model="model"
      :value-schema="typeof objectSchema.additionalProperties === 'object' ? objectSchema.additionalProperties : {}"
      :defs="defs"
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

const props = defineProps<{ objectSchema: Record<string, unknown>; defs?: Record<string, unknown>; fieldKey: string; modelValue?: unknown }>();
const emit = defineEmits<{ "update:modelValue": [v: unknown] }>();

const model = computed({
  get: () => props.modelValue ?? {},
  set: (v) => emit("update:modelValue", v),
});
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
