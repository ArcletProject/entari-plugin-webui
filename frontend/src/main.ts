import { createApp } from 'vue';
import { createPinia } from 'pinia';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate';

import App from './App.vue';
import router from './router';
import initRuntime from './api/runtime';

import './styles/index.scss';
import './styles/theme.scss';
import 'element-plus/theme-chalk/dark/css-vars.css';

(async () => {
  await initRuntime();

  const app = createApp(App);
  const pinia = createPinia();
  pinia.use(piniaPluginPersistedstate);

  app.use(pinia);
  app.use(router);
  app.mount('#app');
})();