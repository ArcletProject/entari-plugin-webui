# 侧边栏动画优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 优化侧边栏收缩/展开动画，实现平滑过渡、快速响应、内容同步

**Architecture:** 使用纯CSS过渡动画，修改Default.vue组件和全局样式，添加collapse状态持久化

**Tech Stack:** Vue 3, Element Plus, CSS Transition, localStorage

---

## 文件结构

- `frontend/src/styles/main.css` - 添加全局动画样式
- `frontend/src/layouts/Default.vue` - 修改侧边栏组件
- `frontend/src/stores/sidebar.ts` - 新建sidebar状态管理（可选）

## 任务分解

### Task 1: 添加全局CSS过渡样式

**Files:**
- Modify: `frontend/src/styles/main.css`

- [ ] **Step 1: 添加el-aside过渡样式**

```css
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: var(--el-font-family);
}

* {
  box-sizing: border-box;
}

.el-aside {
  transition: width 300ms cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.el-menu-item {
  white-space: nowrap;
}
```

- [ ] **Step 2: 验证样式生效**

在浏览器中打开开发者工具，检查`.el-aside`元素是否应用了transition样式。

- [ ] **Step 3: 提交更改**

```bash
git add frontend/src/styles/main.css
git commit -m "style: add sidebar transition animation"
```

### Task 2: 修改Default.vue添加logo过渡

**Files:**
- Modify: `frontend/src/layouts/Default.vue:1-10`

- [ ] **Step 1: 修改logo部分添加transition**

```vue
<template>
  <el-container style="height:100vh">
    <el-aside :width="collapsed ? '64px' : '220px'">
      <transition name="logo-fade" mode="out-in">
        <div class="logo" :key="collapsed">{{ collapsed ? "E" : "Entari" }}</div>
      </transition>
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
      <el-main><slot /></el-main>
    </el-container>
  </el-container>
</template>
```

- [ ] **Step 2: 添加logo过渡样式**

在`<style scoped>`部分添加：

```css
.logo-fade-enter-active,
.logo-fade-leave-active {
  transition: opacity 200ms ease;
}
.logo-fade-enter-from,
.logo-fade-leave-to {
  opacity: 0;
}
```

- [ ] **Step 3: 验证logo过渡效果**

点击折叠按钮，检查logo文字是否平滑过渡。

- [ ] **Step 4: 提交更改**

```bash
git add frontend/src/layouts/Default.vue
git commit -m "feat: add logo transition animation"
```

### Task 3: 添加collapse状态持久化

**Files:**
- Modify: `frontend/src/layouts/Default.vue:30-48`

- [ ] **Step 1: 修改script部分添加localStorage持久化**

```typescript
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
```

- [ ] **Step 2: 验证持久化功能**

1. 展开侧边栏
2. 刷新页面
3. 检查侧边栏是否保持展开状态

- [ ] **Step 3: 提交更改**

```bash
git add frontend/src/layouts/Default.vue
git commit -m "feat: persist sidebar collapsed state"
```

### Task 4: 优化el-menu动画同步

**Files:**
- Modify: `frontend/src/styles/main.css`

- [ ] **Step 1: 检查Element Plus el-menu动画曲线**

在浏览器开发者工具中检查el-menu的transition属性，确认其cubic-bezier值。

- [ ] **Step 2: 如需要，覆盖el-menu动画**

```css
.el-aside {
  transition: width 300ms cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.el-menu {
  transition: width 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

.el-menu-item {
  white-space: nowrap;
}
```

- [ ] **Step 3: 验证动画同步**

点击折叠按钮，检查el-aside和el-menu的动画是否同步。

- [ ] **Step 4: 提交更改**

```bash
git add frontend/src/styles/main.css
git commit -m "style: sync el-menu transition with sidebar"
```

### Task 5: 测试和验证

**Files:**
- None (testing only)

- [ ] **Step 1: 桌面端测试**

1. 打开浏览器开发者工具
2. 点击折叠按钮多次
3. 检查动画是否流畅（60fps）
4. 检查是否有内容溢出

- [ ] **Step 2: 移动端测试**

1. 使用浏览器开发者工具模拟移动设备
2. 测试动画性能
3. 确保无卡顿

- [ ] **Step 3: 状态持久化测试**

1. 展开侧边栏
2. 刷新页面
3. 检查状态是否保持

- [ ] **Step 4: 最终提交**

```bash
git add -A
git commit -m "feat: optimize sidebar animation with smooth transitions"
```