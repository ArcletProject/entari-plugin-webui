<template>
  <div class="panel-host">
    <iframe ref="frame" :src="page.component_url" sandbox="allow-scripts allow-forms" @load="onLoad"></iframe>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import api from "@/api/client";

const props = defineProps<{ page: any }>();
const frame = ref<HTMLIFrameElement>();
let handler: ((e: MessageEvent) => void) | null = null;

function postToChild(msg: any) {
  frame.value?.contentWindow?.postMessage(msg, "*");
}

onMounted(() => {
  handler = async (e: MessageEvent) => {
    if (e.source !== frame.value?.contentWindow) return;
    const { id, method, payload } = e.data || {};
    if (!id || !method) return;
    try {
      let result: any;
      if (method === "api") {
        const r = await api.request(payload);
        result = r.data;
      } else if (method === "user") {
        result = { user: "admin" };
      } else if (method === "ws") {
        result = { url: payload.url };
      } else {
        result = { error: "unknown_method" };
      }
      postToChild({ id, result });
    } catch (err: any) {
      postToChild({ id, error: err.message || "error" });
    }
  };
  window.addEventListener("message", handler);
});
onUnmounted(() => {
  if (handler) window.removeEventListener("message", handler);
});
function onLoad() {
  postToChild({ type: "webui.ready" });
}
</script>
<style scoped>
.panel-host { width: 100%; height: 100%; }
iframe { width: 100%; height: 100%; border: none; border-radius: 8px; }
</style>
