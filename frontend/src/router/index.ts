import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const routes: RouteRecordRaw[] = [
  { path: "/", component: () => import("@/views/Dashboard.vue"), meta: { layout: "default" } },
  { path: "/login", component: () => import("@/views/Login.vue"), meta: { layout: "blank" } },
  { path: "/settings", component: () => import("@/views/Settings.vue"), meta: { layout: "default", label_key: "menu.settings" } },
  { path: "/config", redirect: "/settings" },
  { path: "/plugins", redirect: "/settings" },
  { path: "/market", component: () => import("@/views/Market.vue"), meta: { layout: "default", label_key: "menu.market" } },
  { path: "/logs", component: () => import("@/views/Logs.vue"), meta: { layout: "default", label_key: "menu.logs" } },
  { path: "/chat", component: () => import("@/views/Chat.vue"), meta: { layout: "default", label_key: "menu.chat" } },
  { path: "/extension/:key", component: () => import("@/views/ExtensionPage.vue"), meta: { layout: "default" } },
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
