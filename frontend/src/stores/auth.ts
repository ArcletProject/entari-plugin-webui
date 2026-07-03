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
