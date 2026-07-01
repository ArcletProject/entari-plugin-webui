<template><div class="arr-field">
  <!-- 简单字符串数组 -->
  <el-dynamic-input v-if="isSimpleString" v-model="model" />
  <!-- 对象数组 -->
  <div v-else-if="isObjectItems">
    <el-card v-for="(_, i) in model" :key="i" closable @close="model.splice(i,1)" style="margin-bottom:8px">
      <ObjectField :object-schema="itemsSchema" :defs="defs" :field-key="`${fieldKey}[${i}]`" v-model="model[i]" />
    </el-card>
    <el-button @click="model.push({})">添加项目</el-button>
  </div>
  <!-- oneOf 数组 -->
  <div v-else-if="isOneOfItems">
    <el-card v-for="(_, i) in model" :key="i" closable @close="model.splice(i,1)" style="margin-bottom:8px">
      <OneOfField :one-of="itemsSchema.oneOf" :defs="defs" :field-key="`${fieldKey}[${i}]`" v-model="model[i]" />
    </el-card>
    <el-button @click="model.push({})">添加项目</el-button>
  </div>
  <el-input v-else v-model="jsonText" type="textarea" :rows="4" />
</div></template>
<script setup lang="ts">
import { computed, ref } from "vue";
import ObjectField from "./ObjectField.vue";
import OneOfField from "./OneOfField.vue";
const props = defineProps<{ itemsSchema?: any; defs?: any; fieldKey: string; modelValue?: any[] }>();
const emit = defineEmits<{ "update:modelValue": [v: any[]] }>();
const model = computed<any[]>({ get: () => props.modelValue ?? [], set: (v) => emit("update:modelValue", v) });
const isSimpleString = computed(() => props.itemsSchema?.type === "string");
const isObjectItems = computed(() => props.itemsSchema?.type === "object" && !props.itemsSchema?.oneOf);
const isOneOfItems = computed(() => !!props.itemsSchema?.oneOf);
const jsonText = ref(JSON.stringify(props.modelValue ?? [], null, 2));
</script>
