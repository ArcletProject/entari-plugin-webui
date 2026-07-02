import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import "element-plus/theme-chalk/dark/css-vars.css";
import App from "./App.vue";
import router from "./router";
import i18n from "./i18n";
import "./styles/main.css";
import ECharts from "vue-echarts";
import "echarts";
import editorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import jsonWorker from "monaco-editor/esm/vs/language/json/json.worker?worker";

(self as any).MonacoEnvironment = {
  getWorker(_moduleId: string, label: string) {
    if (label === "json") {
      return new jsonWorker();
    }
    return new editorWorker();
  },
};

const app = createApp(App);
app.use(createPinia()).use(router).use(i18n).use(ElementPlus);
app.component("v-chart", ECharts);
app.mount("#app");
