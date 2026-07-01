<template>
  <el-descriptions :column="1" border>
    <el-descriptions-item label="ID">{{ plugin.id }}</el-descriptions-item>
    <el-descriptions-item label="版本">{{ plugin.version }}</el-descriptions-item>
    <el-descriptions-item label="License">{{ plugin.license || "-" }}</el-descriptions-item>
    <el-descriptions-item label="作者">{{ authors }}</el-descriptions-item>
    <el-descriptions-item label="描述">{{ plugin.description || "-" }}</el-descriptions-item>
    <el-descriptions-item label="URL" v-if="urls.length">
      <div v-for="u in urls" :key="u"><el-link :href="u" target="_blank" type="primary">{{ u }}</el-link></div>
    </el-descriptions-item>
    <el-descriptions-item label="引用" v-if="plugin.references?.length">
      <el-tag v-for="r in plugin.references" :key="r" size="small" style="margin-right:4px">{{ r }}</el-tag>
    </el-descriptions-item>
    <el-descriptions-item label="被引用" v-if="plugin.referents?.length">
      <el-tag v-for="r in plugin.referents" :key="r" size="small" type="info" style="margin-right:4px">{{ r }}</el-tag>
    </el-descriptions-item>
  </el-descriptions>
</template>
<script setup lang="ts">
import { computed } from "vue";
const props = defineProps<{ plugin: any }>();
const authors = computed(() => {
  const a = props.plugin.authors;
  if (!a) return "-";
  return Array.isArray(a) ? a.join(", ") : String(a);
});
const urls = computed(() => {
  const u = props.plugin.urls;
  if (!u) return [];
  return Array.isArray(u) ? u : [u];
});
</script>
