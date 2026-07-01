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

const app = createApp(App);
app.use(createPinia()).use(router).use(i18n).use(ElementPlus);
app.component("v-chart", ECharts);
app.mount("#app");
