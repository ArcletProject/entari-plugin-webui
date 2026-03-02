<template>
  <n-config-provider :theme="theme" :locale="zhCN" :date-locale="dateZhCN">
    <n-loading-bar-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-message-provider>
            <n-layout has-sider class="layout-container">
              <!-- 侧边栏 -->
              <n-layout-sider
                bordered
                collapse-mode="width"
                :collapsed-width="64"
                :width="240"
                :collapsed="collapsed"
                show-trigger
                @collapse="collapsed = true"
                @expand="collapsed = false"
              >
                <!-- Logo -->
                <div class="logo">
                  <Icon name="mdi:robot" size="32" />
                  <span v-show="!collapsed" class="logo-text">Entari</span>
                </div>

                <!-- 导航菜单 -->
                <n-menu
                  :collapsed="collapsed"
                  :collapsed-width="64"
                  :collapsed-icon-size="22"
                  :options="menuOptions"
                  :value="activeMenu"
                  @update:value="handleMenuSelect"
                />
              </n-layout-sider>

              <!-- 主内容区 -->
              <n-layout>
                <!-- 顶部栏 -->
                <n-layout-header bordered class="header">
                  <div class="header-left">
                    <n-breadcrumb>
                      <n-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
                        {{ item.label }}
                      </n-breadcrumb-item>
                    </n-breadcrumb>
                  </div>

                  <div class="header-right">
                    <!-- 暗黑模式切换 -->
                    <n-button quaternary circle @click="toggleColorMode">
                      <template #icon>
                        <Icon :name="colorMode.value === 'dark' ? 'mdi:weather-sunny' : 'mdi:weather-night'" />
                      </template>
                    </n-button>

                    <!-- 用户菜单 -->
                    <n-dropdown
                      v-if="!auth.localMode.value"
                      :options="userMenuOptions"
                      @select="handleUserMenuSelect"
                    >
                      <n-button quaternary>
                        <template #icon>
                          <Icon name="mdi:account-circle" />
                        </template>
                        管理员
                      </n-button>
                    </n-dropdown>
                  </div>
                </n-layout-header>

                <!-- 内容区 -->
                <n-layout-content class="content">
                  <slot />
                </n-layout-content>
              </n-layout>
            </n-layout>
          </n-message-provider>
        </n-notification-provider>
      </n-dialog-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { darkTheme, zhCN, dateZhCN, type MenuOption } from 'naive-ui'

const route = useRoute()
const router = useRouter()
const colorMode = useColorMode()
const auth = useAuth()
const api = useApi()

// 侧边栏折叠状态
const collapsed = ref(false)

// 主题
const theme = computed(() => {
  return colorMode.value === 'dark' ? darkTheme : null
})

// 切换颜色模式
const toggleColorMode = () => {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}

// 菜单数据
const menus = ref<any[]>([])

// 加载菜单
const loadMenus = async () => {
  try {
    const response = await api.get<{ success: boolean; menus: any[] }>('/menus')
    if (response.success) {
      menus.value = response.menus
    }
  } catch {
    // 使用默认菜单
    menus.value = [
      { label: '仪表盘', icon: 'mdi:view-dashboard', path: '/', order: 0 },
      { label: '插件管理', icon: 'mdi:puzzle', path: '/plugins', order: 10 },
      { label: '插件市场', icon: 'mdi:store', path: '/market', order: 20 },
      { label: '配置管理', icon: 'mdi:cog', path: '/config', order: 30 },
      { label: '实时日志', icon: 'mdi:console', path: '/logs', order: 40 },
    ]
  }
}

// 转换为 Naive UI 菜单格式
const menuOptions = computed<MenuOption[]>(() => {
  return menus.value.map(menu => ({
    label: menu.label,
    key: menu.path,
    icon: () => h(resolveComponent('Icon'), { name: menu.icon, size: '20' }),
  }))
})

// 当前激活的菜单
const activeMenu = computed(() => {
  return route.path
})

// 面包屑
const breadcrumbs = computed(() => {
  const current = menus.value.find(m => m.path === route.path)
  if (current) {
    return [
      { label: 'Entari', path: '/' },
      { label: current.label, path: current.path },
    ]
  }
  return [{ label: 'Entari', path: '/' }]
})

// 菜单选择
const handleMenuSelect = (key: string) => {
  router.push(key)
}

// 用户菜单
const userMenuOptions = [
  { label: '修改密码', key: 'password' },
  { label: '退出登录', key: 'logout' },
]

const handleUserMenuSelect = (key: string) => {
  if (key === 'logout') {
    auth.logout()
    router.push('/login')
  } else if (key === 'password') {
    // TODO: 打开修改密码对话框
  }
}

// 初始化
onMounted(() => {
  loadMenus()
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 64px;
  font-size: 20px;
  font-weight: bold;
}

.logo-text {
  transition: opacity 0.3s;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.content {
  padding: 24px;
  height: calc(100vh - 64px);
  overflow: auto;
}
</style>
