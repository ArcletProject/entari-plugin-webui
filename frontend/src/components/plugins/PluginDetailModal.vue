<template>
  <div class="plugin-detail">
    <el-descriptions
      :column="1"
      border
    >
      <el-descriptions-item label="ID">
        {{ plugin.id }}
      </el-descriptions-item>
      <el-descriptions-item label="版本">
        {{ plugin.version }}
      </el-descriptions-item>
      <el-descriptions-item label="License">
        {{ plugin.license || "-" }}
      </el-descriptions-item>
      <el-descriptions-item label="作者">
        {{ authors }}
      </el-descriptions-item>
      <el-descriptions-item label="描述">
        {{ plugin.description || "-" }}
      </el-descriptions-item>
      <el-descriptions-item
        v-if="urlEntries.length"
        label="URL"
      >
        <div
          v-for="[key, url] in urlEntries"
          :key="key"
        >
          <el-link
            :href="url"
            target="_blank"
            type="primary"
          >
            {{ key }}
          </el-link>
        </div>
      </el-descriptions-item>
      <el-descriptions-item
        v-if="plugin.references?.length"
        label="引用"
      >
        <el-tag
          v-for="r in plugin.references"
          :key="r"
          size="small"
          style="margin-right:4px"
        >
          {{ r }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item
        v-if="plugin.referents?.length"
        label="被引用"
      >
        <el-tag
          v-for="r in plugin.referents"
          :key="r"
          size="small"
          type="info"
          style="margin-right:4px"
        >
          {{ r }}
        </el-tag>
      </el-descriptions-item>
    </el-descriptions>
    <el-divider
      v-if="plugin.readme"
      content-position="left"
    >
      README
    </el-divider>
    <MarkdownViewer
      v-if="plugin.readme"
      :source="plugin.readme"
    />
  </div>
</template>
<script setup lang="ts">
import { computed } from "vue";
import MarkdownViewer from "@/components/common/MarkdownViewer.vue";
interface PluginDetail {
  id: string;
  version?: string;
  license?: string;
  authors?: string | string[];
  description?: string;
  urls?: Record<string, string> | string[];
  references?: string[];
  referents?: string[];
  readme?: string;
}
const props = defineProps<{ plugin: PluginDetail }>();
const authors = computed(() => {
  const a = props.plugin.authors;
  if (!a) return "-";
  return Array.isArray(a) ? a.join(", ") : String(a);
});
const urlEntries = computed(() => {
  const u = props.plugin.urls;
  if (!u) return [];
  if (Array.isArray(u)) return u.map((item, i) => [String(i), item]);
  if (typeof u === "object") return Object.entries(u).filter(([, v]) => v);
  return [];
});
</script>
<style scoped>
.plugin-detail {
  max-height: 70vh;
  overflow: auto;
}
</style>
