/**
 * 认证状态管理
 */

interface AuthState {
  accessToken: string | null
  refreshTokenValue: string | null
  expiresAt: number | null
  localMode: boolean
}

const AUTH_STORAGE_KEY = 'entari_webui_auth'

export const useAuth = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  // 状态
  const accessToken = useState<string | null>('auth_access_token', () => null)
  const refreshTokenValue = useState<string | null>('auth_refresh_token', () => null)
  const expiresAt = useState<number | null>('auth_expires_at', () => null)
  const localMode = useState<boolean>('auth_local_mode', () => false)
  const initialized = useState<boolean>('auth_initialized', () => false)

  // 从 localStorage 恢复状态
  const restore = () => {
    if (import.meta.client) {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY)
      if (stored) {
        try {
          const data: AuthState = JSON.parse(stored)
          accessToken.value = data.accessToken
          refreshTokenValue.value = data.refreshTokenValue
          expiresAt.value = data.expiresAt
          localMode.value = data.localMode
        } catch {
          localStorage.removeItem(AUTH_STORAGE_KEY)
        }
      }
    }
  }

  // 保存状态到 localStorage
  const persist = () => {
    if (import.meta.client) {
      const data: AuthState = {
        accessToken: accessToken.value,
        refreshTokenValue: refreshTokenValue.value,
        expiresAt: expiresAt.value,
        localMode: localMode.value,
      }
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data))
    }
  }

  // 检查认证模式
  const checkAuthMode = async (): Promise<boolean> => {
    try {
      const response = await fetch(`${apiBase}/auth/check`)
      const data = await response.json()
      localMode.value = data.local_mode
      initialized.value = true
      persist()
      return data.local_mode
    } catch {
      return false
    }
  }

  // 登录
  const login = async (password: string): Promise<{ success: boolean; message?: string }> => {
    try {
      const response = await fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      const data = await response.json()

      if (data.success) {
        accessToken.value = data.access_token
        refreshTokenValue.value = data.refresh_token
        expiresAt.value = Date.now() + data.expires_in * 1000
        persist()
        return { success: true }
      }

      return { success: false, message: data.message || '登录失败' }
    } catch (e) {
      return { success: false, message: '网络错误' }
    }
  }

  // 刷新 token
  const refreshToken = async (): Promise<boolean> => {
    if (!refreshTokenValue.value) {
      return false
    }

    try {
      const response = await fetch(`${apiBase}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshTokenValue.value }),
      })
      const data = await response.json()

      if (data.success) {
        accessToken.value = data.access_token
        refreshTokenValue.value = data.refresh_token
        expiresAt.value = Date.now() + data.expires_in * 1000
        persist()
        return true
      }

      return false
    } catch {
      return false
    }
  }

  // 登出
  const logout = () => {
    accessToken.value = null
    refreshTokenValue.value = null
    expiresAt.value = null
    if (import.meta.client) {
      localStorage.removeItem(AUTH_STORAGE_KEY)
    }
  }

  // 检查是否已认证
  const isAuthenticated = computed(() => {
    // 本地模式无需认证
    if (localMode.value) {
      return true
    }
    // 检查 token 是否有效
    if (!accessToken.value) {
      return false
    }
    // 检查是否过期
    if (expiresAt.value && Date.now() > expiresAt.value) {
      return false
    }
    return true
  })

  // 初始化
  const init = async () => {
    if (initialized.value) {
      return
    }
    restore()
    await checkAuthMode()
  }

  return {
    accessToken,
    refreshTokenValue,
    expiresAt,
    localMode,
    initialized,
    isAuthenticated,
    init,
    restore,
    checkAuthMode,
    login,
    refreshToken,
    logout,
  }
}
