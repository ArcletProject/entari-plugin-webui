<template>
  <div class="extension-page">
    <ExtensionPanelHost
      v-if="page"
      :page="page"
    />
    <el-empty
      v-else
      description="扩展页面不存在"
    />
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import api from "@/api/client";
import ExtensionPanelHost from "@/extension-runtime/ExtensionPanelHost.vue";

interface ExtensionPageDef {
  key: string;
  component_url: string;
}

const route = useRoute();
const pages = ref<ExtensionPageDef[]>([]);
const page = computed(() => pages.value.find((p) => p.key === route.params.key));

onMounted(async () => {
  const r = await api.get("/api/extensions/manifest");
  pages.value = r.data.pages || [];
});
</script>
<style scoped>
.extension-page { height: 100%; padding: 16px; }
</style>
