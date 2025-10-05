import axios from '@/utils/request'

/* ---------- 公共子类型 ---------- */
export type PluginConfig = Record<string, string | number | boolean | string[] | undefined>

export type AuthorItem = { name?: string; email?: string } | string
export type RawAuthor = AuthorItem | AuthorItem[]

export interface PluginMeta {
  name?: string
  version?: string
  author?: RawAuthor
  authors?: RawAuthor
  license?: string
  description?: string
  desc?: string
  urls?: { homepage?: string }
  depend_services?: string[]
  readme?: string
}

/* ---------- 后端返回的原始插件结构 ---------- */
export interface Plugin {
  name: string
  id: string
  title: string
  desc: string
  version: string
  author?: string
  status: boolean
  builtin?: boolean
  urls?: { homepage?: string }
  installed: boolean
  meta?: PluginMeta | null | 'None'
  readme?: string
}

/* ---------- 前端业务层插件类型（在 Plugin 基础上扩展） ---------- */
export interface PluginItem extends Plugin {
  configurable?: boolean
  config?: PluginConfig
}

/* ---------- 市场插件类型 ---------- */
export interface MarketItem {
  name: string
  fullName: string
  desc: string
  author?: string
  version: string
  updated: string
  tags: string[]
  installed: boolean
  readme?: string
  homepage?: string
  meta?: PluginMeta | null | 'None'
  // urls?: { homepage?: string } 
}

/* ---------- API 方法 ---------- */
export const listPlugins = (): Promise<PluginItem[]> =>
  axios.get('/plugins')

export const togglePluginAPI = (id: string, enable: boolean) =>
  axios.post('/plugins/toggle', { id, enable })

export const installPlugin = (name: string) =>
  axios.post('/plugins/install', { name })

export const uninstallPlugin = (name: string) =>
  axios.post('/plugins/uninstall', { name })

export const listMarketPlugins = (): Promise<MarketItem[]> =>
  axios.get('/market/plugins')

export const searchPlugins = (keyword: string): Promise<PluginItem[]> =>
  axios.get(`/plugins/search?q=${keyword}`)

export const loadPlugin = (name: string) =>
  axios.post(`/plugins/load`, { name })

export const unloadPlugin = (name: string) =>
  axios.post(`/plugins/unload`, { name })

export const reloadPlugin = (name: string) =>
  axios.post(`/plugins/reload`, { name })

// 保存插件配置
export const savePlugin = (data: Partial<PluginItem>) =>
  axios.post('/plugins/save', data)
