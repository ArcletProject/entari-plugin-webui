# Phase 09 — 前端骨架与登录

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** 搭 Vite + Vue 3 + Element Plus + Pinia + vue-router + vue-i18n + axios；实现 router 鉴权守卫、auth store、axios 拦截、`useBackendHealth` 心跳与离线遮罩、明暗主题、Default/Blank 布局、Login 页、API client 封装。后端 API 全部就绪，前端从本 phase 开始。

**Architecture:** SPA（非 SSR）；`vite build` 产物输出到 `src/entari_plugin_webui/static/frontend/`；dev server 代理 `/api`、`/ws`。axios `withCredentials` + `X-Requested-With`。三态健康机 `online/reconnecting/offline`。

**Tech Stack:** Vue 3.5、Vite 5、Element Plus、Pinia、vue-router 4、vue-i18n 9、axios、Monaco（phase-10 用，本 phase 装依赖即可）、ECharts（同上）、ansi-to-html（同上）。

---

## 文件结构

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .eslintrc.cjs (可选)
└── src/
    ├── main.ts
    ├── App.vue
    ├── router/index.ts
    ├── pinia setup in main
    ├── stores/auth.ts
    ├── stores/theme.ts
    ├── stores/menu.ts
    ├── api/client.ts
    ├── composables/useBackendHealth.ts
    ├── composables/useApi.ts
    ├── composables/useWebSocket.ts
    ├── i18n/zh-CN.ts
    ├── i18n/index.ts
    ├── layouts/Default.vue
    ├── layouts/Blank.vue
    ├── views/Login.vue
    ├── views/Dashboard.vue (占位)
    ├── components/OfflineOverlay.vue
    ├── components/ThemeToggle.vue
    └── styles/main.css
```

---

## Task 9.1：脚手架与依赖

**Files:** Create `frontend/package.json`、`vite.config.ts`、`tsconfig.json`、`index.html`、`src/main.ts`、`src/App.vue`

- [ ] **Step 1: package.json**

```json
{
  "name": "entari-webui-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext .ts,.vue"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0",
    "pinia": "^2.2.0",
    "element-plus": "^2.8.0",
    "@element-plus/icons-vue": "^2.3.1",
    "vue-i18n": "^9.14.0",
    "axios": "^1.7.0",
    "echarts": "^5.5.0",
    "vue-echarts": "^7.0.0",
    "monaco-editor": "^0.50.0",
    "ansi-to-html": "^0.7.2"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vue-tsc": "^2.1.0",
    "@types/node": "^22.0.0",
    "eslint": "^9.0.0",
    "@vue/eslint-config-typescript": "^14.0.0",
    "eslint-plugin-vue": "^9.28.0"
  }
}
```

- [ ] **Step 2: vite.config.ts**

```ts
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  server: {
    proxy: {
      "/api": { target: "http://127.0.0.1:5150", changeOrigin: true },
      "/ws": { target: "ws://127.0.0.1:5150", ws: true },
    },
  },
  build: {
    outDir: "../src/entari_plugin_webui/static/frontend",
    emptyOutDir: true,
  },
});
```

- [ ] **Step 3: tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "preserve",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "paths": { "@/*": ["./src/*"] },
    "types": ["node"]
  },
  "include": ["src/**/*.ts", "src/**/*.vue", "src/**/*.d.ts"]
}
```

- [ ] **Step 4: index.html / main.ts / App.vue**

```html
<!-- index.html -->
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Entari WebUI</title></head><body><div id="app"></div><script type="module" src="/src/main.ts"></script></body></html>
```

```ts
// src/main.ts
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
```

```vue
<!-- src/App.vue -->
<template>
  <OfflineOverlay />
  <RouterView />
</template>
<script setup lang="ts">
import OfflineOverlay from "@/components/OfflineOverlay.vue";
import { useThemeStore } from "@/stores/theme";
const theme = useThemeStore();
theme.init();
</script>
```

> `vue-echarts` 与 `monaco` 全量导入可能拖慢首屏；phase-10 改为按需。

- [ ] **Step 5:** `cd frontend && npm install`。提交 `git commit -m "chore(frontend): scaffold vite + vue + element plus"`。

---

## Task 9.2：i18n（zh-CN key 化）

**Files:** Create `i18n/zh-CN.ts`、`i18n/index.ts`

- [ ] **Step 1:** 词条覆盖菜单、登录、健康、通用按钮。示例：

```ts
// src/i18n/zh-CN.ts
export default {
  menu: { dashboard: "仪表盘", plugins: "插件管理", market: "插件市场", config: "配置管理", logs: "实时日志" },
  auth: {
    login: "登录", password: "密码", submit: "登录", local_mode: "本地模式", logout: "退出登录",
    change_password: "修改密码", wrong_password: "密码错误", rate_limited: "尝试过于频繁，请稍后再试",
  },
  health: { reconnecting: "正在连接后端…", offline: "后端已断开", retry: "手动重连" },
  common: { save: "保存", cancel: "取消", refresh: "刷新", confirm: "确定" },
};
```

```ts
// src/i18n/index.ts
import { createI18n } from "vue-i18n";
import zhCN from "./zh-CN";

const i18n = createI18n({ legacy: false, locale: "zh-CN", messages: { "zh-CN": zhCN } });
// 扩展词条在 useExtensionsManifest 获取后合并（phase-10/11 实现 mergeLocaleMessage）
export default i18n;
```

- [ ] **Step 2:** 提交。

---

## Task 9.3：stores

**Files:** Create `stores/auth.ts`、`stores/theme.ts`、`stores/menu.ts`

- [ ] **Step 1: auth store**（无 token，仅 localMode + initialized + 会话依赖 Cookie）

```ts
// src/stores/auth.ts
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import api from "@/api/client";

export const useAuthStore = defineStore("auth", () => {
  const localMode = ref(true);
  const initialized = ref(false);
  const inited = ref(false);

  async function init() {
    if (inited.value) return;
    inited.value = true;
    try {
      const r = await api.get("/api/auth/check");
      localMode.value = r.data.local_mode as boolean;
      initialized.value = r.data.initialized as boolean;
    } catch {
      // 后端不可达由 useBackendHealth 处理
    }
  }

  async function login(password: string) {
    const r = await api.post("/api/auth/login", { password });
    return r.data;
  }

  async function logout() {
    await api.post("/api/auth/logout");
  }

  async function changePassword(oldPwd: string, newPwd: string) {
    await api.put("/api/auth/password", { old_password: oldPwd, new_password: newPwd });
  }

  const isAuthenticated = computed(() => localMode.value || true /* 会话存在性由后端 401 判定 */);
  return { localMode, initialized, init, login, logout, changePassword, isAuthenticated };
});
```

- [ ] **Step 2: theme store**

```ts
// src/stores/theme.ts
import { defineStore } from "pinia";
import { ref, watch } from "vue";

export const useThemeStore = defineStore("theme", () => {
  const mode = ref<"light" | "dark">((localStorage.getItem("webui_theme") as any) || "light");
  function init() {
    watch(mode, (v) => {
      localStorage.setItem("webui_theme", v);
      document.documentElement.classList.toggle("dark", v === "dark");
    }, { immediate: true });
  }
  function toggle() { mode.value = mode.value === "light" ? "dark" : "light"; }
  return { mode, init, toggle };
});
```

- [ ] **Step 3: menu store**

```ts
// src/stores/menu.ts
import { defineStore } from "pinia";
import { ref } from "vue";
import api from "@/api/client";

export interface MenuItem { label_key: string; icon: string; path: string; order: number; label?: string; }

export const useMenuStore = defineStore("menu", () => {
  const items = ref<MenuItem[]>([]);
  async function load() {
    const r = await api.get("/api/menus");
    items.value = r.data.menus;
  }
  return { items, load };
});
```

- [ ] **Step 4:** 提交 `git commit -m "feat(frontend): auth/theme/menu stores"`。

---

## Task 9.4：axios client + 拦截

**Files:** Create `api/client.ts`

- [ ] **Step 1:**

```ts
// src/api/client.ts
import axios from "axios";
import router from "@/router";

const client = axios.create({
  baseURL: "",
  withCredentials: true,
  headers: { "X-Requested-With": "XMLHttpRequest" },
  timeout: 15000,
});

client.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      router.push("/login").catch(() => {});
    }
    return Promise.reject(err);
  },
);

export default client;
```

> 网络层失败（`!err.response`）由 `useBackendHealth` 处理，不在此跳转。

- [ ] **Step 2:** 提交。

---

## Task 9.5：useBackendHealth + OfflineOverlay

**Files:** Create `composables/useBackendHealth.ts`、`components/OfflineOverlay.vue`

- [ ] **Step 1: composable**

```ts
// src/composables/useBackendHealth.ts
import { ref } from "vue";
import api from "@/api/client";

export type HealthState = "online" | "reconnecting" | "offline";
const state = ref<HealthState>("online");
let miss = 0;
let timer: number | null = null;
const recoveredCbs = new Set<() => void>();

async function probe(): Promise<boolean> {
  try {
    await api.get("/api/health", { timeout: 2000 });
    return true;
  } catch {
    return false;
  }
}

function set(next: HealthState) {
  if (state.value === next) return;
  state.value = next;
  if (next === "online") {
    recoveredCbs.forEach((cb) => cb());
  }
}

export function useBackendHealth() {
  async function start() {
    if (timer) return;
    timer = window.setInterval(tick, 5000);
    await tick();
  }
  async function tick() {
    const ok = await probe();
    if (ok) { miss = 0; set("online"); return; }
    miss += 1;
    if (miss === 1) set("reconnecting");
    if (miss >= 3) set("offline");
  }
  async function reconnectNow() {
    miss = 0; set("online");
    await tick();
  }
  function onRecovered(cb: () => void) { recoveredCbs.add(cb); return () => recoveredCbs.delete(cb); }
  return { state, start, reconnectNow, onRecovered };
}
```

- [ ] **Step 2: OfflineOverlay.vue**

```vue
<!-- src/components/OfflineOverlay.vue -->
<template>
  <el-overlay v-if="state === 'offline'" :z-index="3000">
    <div class="offline-box">
      <el-icon size="48"><WarnTriangleFilled /></el-icon>
      <h2>{{ t("health.offline") }}</h2>
      <el-button type="primary" @click="reconnectNow()">{{ t("health.retry") }}</el-button>
    </div>
  </el-overlay>
  <div v-else-if="state === 'reconnecting'" class="reconnecting-banner">
    {{ t("health.reconnecting") }}
  </div>
</template>
<script setup lang="ts">
import { onMounted } from "vue";
import { useBackendHealth } from "@/composables/useBackendHealth";
import { WarnTriangleFilled } from "@element-plus/icons-vue";
import { useI18n } from "vue-i18n";
const { state, start, reconnectNow } = useBackendHealth();
const { t } = useI18n();
onMounted(() => { start(); });
</script>
<style scoped>
.offline-box { display:flex; flex-direction:column; align-items:center; gap:16px; color:#fff; }
.reconnecting-banner { position:fixed; top:0; left:0; right:0; background:var(--el-color-warning); color:#fff; text-align:center; padding:4px; z-index:2000; }
</style>
```

- [ ] **Step 3:** 提交 `git commit -m "feat(frontend): backend health heartbeat + offline overlay"`。

---

## Task 9.6：router + 守卫

**Files:** Create `router/index.ts`

- [ ] **Step 1:**

```ts
// src/router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const routes: RouteRecordRaw[] = [
  { path: "/", component: () => import("@/views/Dashboard.vue"), meta: { layout: "default" } },
  { path: "/login", component: () => import("@/views/Login.vue"), meta: { layout: "blank" } },
  { path: "/plugins", component: () => import("@/views/Placeholder.vue"), meta: { layout: "default", label_key: "menu.plugins" } },
  { path: "/market", component: () => import("@/views/Placeholder.vue"), meta: { layout: "default" } },
  { path: "/config", component: () => import("@/views/Placeholder.vue"), meta: { layout: "default" } },
  { path: "/logs", component: () => import("@/views/Placeholder.vue"), meta: { layout: "default" } },
];

const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach(async (to) => {
  if (to.path === "/login") return true;
  const auth = useAuthStore();
  await auth.init();
  if (auth.localMode) return true;
  // 远程模式：无 401 即视为已会话
  return true;
});

router.onError((err) => {
  // 网络错误由健康心跳处理
  console.warn("router error", err);
});

export default router;

async function _nav(path: string) { return router.push(path); }
export { _nav };
```

> `Placeholder.vue` 在 phase-10 替换为真实页面；先建占位：

```vue
<!-- src/views/Placeholder.vue --><template><el-empty description="coming soon" /></template>
```

- [ ] **Step 2:** 提交 `git commit -m "feat(frontend): router and auth guard"`。

---

## Task 9.7：layouts + ThemeToggle + Login + Dashboard 占位

**Files:** Create `layouts/Default.vue`、`layouts/Blank.vue`、`components/ThemeToggle.vue`、`views/Login.vue`、`views/Dashboard.vue`

- [ ] **Step 1: Default layout**（侧边栏 + 头部 + 管理员菜单）

```vue
<!-- src/layouts/Default.vue -->
<template>
  <el-container style="height:100vh">
    <el-aside :width="collapsed ? '64px' : '220px'">
      <div class="logo">{{ collapsed ? "E" : "Entari" }}</div>
      <el-menu :default-active="route.path" :collapse="collapsed" router>
        <el-menu-item v-for="m in menu.items" :key="m.path" :index="m.path">
          <el-icon><Icon :icon="m.icon" /></el-icon>
          <template #title>{{ t(m.label_key) }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-button text @click="collapsed = !collapsed"><el-icon><Fold /></el-icon></el-button>
        <div class="spacer"></div>
        <ThemeToggle />
        <el-dropdown v-if="!auth.localMode">
          <el-button text>{{ t("auth.logout") }}</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="doLogout">{{ t("auth.logout") }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main><RouterView /></el-main>
    </el-container>
  </el-container>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { Fold } from "@element-plus/icons-vue";
import Icon from "@/components/AppIcon.vue"; // 简单 Iconify 包装（见下）
import ThemeToggle from "@/components/ThemeToggle.vue";
import { useMenuStore } from "@/stores/menu";
import { useAuthStore } from "@/stores/auth";

const menu = useMenuStore();
const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const collapsed = ref(false);
onMounted(() => { menu.load(); });
async function doLogout() { await auth.logout(); router.push("/login"); }
</script>
```

> `AppIcon.vue`：图标用 `@iconify-json/mdi`？为减依赖，本 phase 用 Element Plus 图标即可——直接在 menu.icon 映射 Element 图标组件；或简单 `<i :class>`. 为简化，建 `AppIcon.vue` 接受 `icon` 字符串并渲染 `<el-icon>` 内嵌 SVG fallback。phase-10 再补图标体系。

```vue
<!-- src/components/AppIcon.vue -->
<template><el-icon><component :is="comp" /></el-icon></template>
<script setup lang="ts">
import { computed } from "vue";
const props = defineProps<{ icon: string }>();
const map: Record<string, any> = () => import("@element-plus/icons-vue");
const comp = computed(() => null); // TODO phase-10：图标映射
</script>
```

> 简化：先不渲染图标，phase-10 引入 `@iconify/vue` 完整方案。

- [ ] **Step 2: Blank layout**（居中）

```vue
<template><div class="blank"><slot /></div></template>
<style scoped>.blank{display:flex;align-items:center;justify-content:center;height:100vh;}</style>
```

- [ ] **Step 3: ThemeToggle.vue**

```vue
<template><el-button text @click="theme.toggle()"><el-icon><Sunny v-if="theme.mode==='light'"/><Moon v-else/></el-icon></el-button></template>
<script setup lang="ts">import { Sunny, Moon } from "@element-plus/icons-vue"; import { useThemeStore } from "@/stores/theme"; const theme = useThemeStore();</script>
```

- [ ] **Step 4: Login.vue**

```vue
<!-- src/views/Login.vue -->
<template>
  <div class="login-card">
    <h2>{{ t("auth.login") }}</h2>
    <el-form @submit.prevent="onSubmit" v-loading="loading">
      <el-form-item :label="t('auth.password')" v-if="!auth.localMode">
        <el-input v-model="password" type="password" show-password @keyup.enter="onSubmit" />
      </el-form-item>
      <el-button type="primary" :loading="loading" @click="onSubmit">{{ t("auth.submit") }}</el-button>
    </el-form>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useI18n } from "vue-i18n";
import { useAuthStore } from "@/stores/auth";
const auth = useAuthStore();
const router = useRouter();
const { t } = useI18n();
const password = ref("");
const loading = ref(false);
onMounted(async () => { await auth.init(); if (auth.localMode) router.replace("/"); });
async function onSubmit() {
  loading.value = true;
  try { await auth.login(password.value); router.replace("/"); }
  catch (e: any) {
    const status = e.response?.status;
    ElMessage.error(status === 429 ? t("auth.rate_limited") : status === 401 ? t("auth.wrong_password") : e.message);
  } finally { loading.value = false; }
}
</script>
<style scoped>.login-card{width:320px;padding:24px;background:var(--el-bg-color);border-radius:8px;box-shadow:var(--el-box-shadow-light);}</style>
```

> 远程模式首次访问 `/login` 已能登录（后端 `/api/auth/login` 返回含 Cookie）。本地模式直接跳首页。

- [ ] **Step 5: Dashboard.vue 占位**

```vue
<template><el-empty :description="t('menu.dashboard')" /></template>
<script setup lang="ts">import { useI18n } from "vue-i18n"; const { t } = useI18n();</script>
```

- [ ] **Step 6:** `cd frontend && npm run build`，验证产物写入 `static/frontend/`。提交 `git commit -m "feat(frontend): layouts, login, dashboard placeholder"`.

---

## Task 9.8：布局应用到路由

`App.vue` 根据 `route.meta.layout` 包 Default/Blank：

```vue
<!-- src/App.vue 重写 -->
<template>
  <OfflineOverlay />
  <component :is="layout"><RouterView /></component>
</template>
<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import Default from "@/layouts/Default.vue";
import Blank from "@/layouts/Blank.vue";
import OfflineOverlay from "@/components/OfflineOverlay.vue";
const route = useRoute();
const layout = computed(() => (route.meta.layout === "blank" ? Blank : Default));
import { useThemeStore } from "@/stores/theme";
useThemeStore().init();
</script>
```

提交。

---

## Phase 9 完成标准

- `cd frontend && npm run build` 成功，产物写入 `src/entari_plugin_webui/static/frontend/`
- 本地模式：访问 `/` 经健康探针后进入 Default 布局；远程模式：访问跳 `/login`，登录后跳首页
- 离线时全屏遮罩，可手动重连
- 明暗主题切换生效
- eslint（如配置）无错；构建无 TS 错