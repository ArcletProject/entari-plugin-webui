<template>
  <el-container style="height:100vh">
    <el-aside
      :width="collapsed ? '64px' : '220px'"
      class="sidebar"
    >
      <transition
        name="logo-fade"
        mode="out-in"
      >
        <div
          :key="String(collapsed)"
          class="logo"
        >
          <img
            src="@/assets/logo.svg"
            class="logo-img"
          >
          <span
            v-if="!collapsed"
            class="logo-text"
          >Entari</span>
        </div>
      </transition>
      <el-menu
        :default-active="route.path"
        :collapse="collapsed"
        router
      >
        <el-menu-item
          v-for="m in menu.items"
          :key="m.path"
          :index="m.path"
        >
          <el-icon><Icon :icon="m.icon" /></el-icon>
          <template #title>
            {{ m.label || t(m.label_key) }}
          </template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-button
          text
          @click="collapsed = !collapsed"
        >
          <el-icon><Fold /></el-icon>
        </el-button>
        <div class="spacer" />
        <ThemeToggle />
        <el-dropdown v-if="!auth.localMode">
          <el-button text>
            {{ t("auth.logout") }}
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="doLogout">
                {{ t("auth.logout") }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main><slot /></el-main>
    </el-container>
  </el-container>
</template>
<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { Fold } from "@element-plus/icons-vue";
import Icon from "@/components/AppIcon.vue";
import ThemeToggle from "@/components/ThemeToggle.vue";
import { useMenuStore } from "@/stores/menu";
import { useAuthStore } from "@/stores/auth";

const menu = useMenuStore();
const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const collapsed = ref(localStorage.getItem("webui_sidebar_collapsed") === "true");

watch(collapsed, (val) => {
  localStorage.setItem("webui_sidebar_collapsed", String(val));
});

onMounted(() => { menu.load(); });
async function doLogout() { await auth.logout(); router.push("/login"); }
</script>
<style scoped>
.sidebar {
  border-right: 1px solid var(--el-border-color);
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-weight: bold;
  font-size: 20px;
  border-bottom: 1px solid var(--el-border-color);
}
.logo-img {
  width: 32px;
  height: 32px;
}
.logo-text {
  white-space: nowrap;
}
.header {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--el-border-color);
}
.spacer { flex: 1; }
.logo-fade-enter-active,
.logo-fade-leave-active {
  transition: opacity 200ms ease;
}
.logo-fade-enter-from,
.logo-fade-leave-to {
  opacity: 0;
}
</style>
