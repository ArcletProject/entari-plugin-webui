/**
 * API 请求封装
 */

interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  [key: string]: any
}

interface AuthTokens {
  access_token: string
  refresh_token: string
  expires_in: number
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string
  const auth = useAuth()

  /**
   * 发起 API 请求
   */
  const request = async <T = any>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> => {
    const url = `${apiBase}${path}`

    // 添加认证头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }

    if (auth.accessToken.value) {
      headers['Authorization'] = `Bearer ${auth.accessToken.value}`
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    // 处理 401 错误
    if (response.status === 401) {
      // 尝试刷新 token
      const refreshed = await auth.refreshToken()
      if (refreshed) {
        // 重试请求
        headers['Authorization'] = `Bearer ${auth.accessToken.value}`
        const retryResponse = await fetch(url, { ...options, headers })
        return retryResponse.json()
      } else {
        // 刷新失败，跳转登录
        auth.logout()
        navigateTo('/login')
        throw new Error('认证已过期')
      }
    }

    return response.json()
  }

  /**
   * GET 请求
   */
  const get = <T = any>(path: string): Promise<T> => {
    return request<T>(path, { method: 'GET' })
  }

  /**
   * POST 请求
   */
  const post = <T = any>(path: string, data?: any): Promise<T> => {
    return request<T>(path, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * PUT 请求
   */
  const put = <T = any>(path: string, data?: any): Promise<T> => {
    return request<T>(path, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * DELETE 请求
   */
  const del = <T = any>(path: string): Promise<T> => {
    return request<T>(path, { method: 'DELETE' })
  }

  return {
    request,
    get,
    post,
    put,
    del,
  }
}

export type { ApiResponse, AuthTokens }
