<template>
  <div class="dual-editor">
    <el-radio-group v-model="view">
      <el-radio-button label="form">表单</el-radio-button>
      <el-radio-button label="code">代码</el-radio-button>
    </el-radio-group>
    <el-alert v-if="codeInvalid && view==='form'" type="warning" :title="t('config.code_invalid_note')" :closable="false" />
    <SchemaForm v-show="view==='form'" :schema="schema" v-model="formData" />
    <div v-show="view==='code'" ref="monacoHost" style="height:480px"></div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import * as monaco from "monaco-editor";
import SchemaForm from "@/components/schema-form/SchemaForm.vue";
import { useI18n } from "vue-i18n";

const props = defineProps<{ schema: any; modelValue: any; lang?: "json" | "yaml" }>();
const emit = defineEmits<{ "update:modelValue": [v: any] }>();
const { t } = useI18n();
const view = ref<"form" | "code">("form");
const formData = ref<any>(props.modelValue ?? {});
const codeInvalid = ref(false);
const monacoHost = ref<HTMLElement>();
let editor: monaco.editor.IStandaloneCodeEditor | null = null;

watch(formData, (v) => emit("update:modelValue", v), { deep: true });

// 离开代码视图 → 解析覆盖表单
watch(view, (v, old) => {
  if (old === "code" && v === "form" && editor) {
    try {
      const parsed = props.lang === "yaml" ? parseYaml(editor.getValue()) : JSON.parse(editor.getValue());
      formData.value = parsed;
      codeInvalid.value = false;
    } catch { codeInvalid.value = true; }
  }
  if (v === "code") {
    // 表单 → 代码：以表单序列化覆盖代码内容
    nextTick(() => syncMonaco());
  }
});

function parseYaml(s: string) { /* 用 js-yaml 或简陋解析；首版仅 JSON，YAML 见 §6.3 后续 */
  return JSON.parse(s);
}

function syncMonaco() {
  if (!editor) return;
  const text = JSON.stringify(formData.value, null, 2);
  editor.setValue(text);
}

onMounted(() => {
  if (!monacoHost.value) return;
  editor = monaco.editor.create(monacoHost.value, {
    value: JSON.stringify(formData.value, null, 2),
    language: props.lang === "yaml" ? "yaml" : "json",
    automaticLayout: true,
  });
});
onBeforeUnmount(() => editor?.dispose());
</script>
<style scoped>
.dual-editor { display: flex; flex-direction: column; gap: 12px; }
</style>
