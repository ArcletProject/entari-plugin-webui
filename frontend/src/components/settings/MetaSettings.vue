<template>
  <el-card
    v-if="schema"
    class="meta-card"
  >
    <template #header>
      <div
        class="card-header collapsible"
        @click="open = !open"
      >
        <span>元数据设置</span>
        <el-icon :class="{ 'is-reverse': open }">
          <ArrowUpBold />
        </el-icon>
      </div>
    </template>
    <div v-show="open">
      <SchemaForm
        v-if="patchedSchema"
        v-model="model"
        :schema="patchedSchema"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { ArrowUpBold } from "@element-plus/icons-vue";
import SchemaForm from "@/components/schema-form/SchemaForm.vue";

const props = defineProps<{ schema: Record<string, unknown> | null; modelValue: Record<string, unknown> }>();
const open = ref(true);
const emit = defineEmits<{ "update:modelValue": [value: Record<string, unknown>] }>();
const { t } = useI18n();

const patchedSchema = computed(() => {
  if (!props.schema) return null;
  const properties: Record<string, Record<string, unknown>> = {};
  for (const [key, prop] of Object.entries(props.schema.properties ?? {})) {
    const p = prop as Record<string, unknown>;
    const label = t(`meta.${key}`);
    properties[key] = label && !label.startsWith("meta.") ? { ...p, title: label } : { ...p };
  }
  return { ...props.schema, properties };
});

const model = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});
</script>

<style scoped>
.meta-card {
  margin-bottom: 16px;
  background: var(--el-fill-color-light);
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.collapsible {
  cursor: pointer;
  user-select: none;
}
.el-icon.is-reverse {
  transform: rotate(180deg);
}
</style>
