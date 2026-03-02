/**
 * 全局认证中间件
 */
export default defineNuxtRouteMiddleware(async (to, from) => {
  // 跳过登录页
  if (to.path === '/login') {
    return
  }

  const auth = useAuth()

  // 初始化认证状态
  await auth.init()

  // 本地模式无需认证
  if (auth.localMode.value) {
    return
  }

  // 检查是否已认证
  if (!auth.isAuthenticated.value) {
    return navigateTo('/login')
  }
})
