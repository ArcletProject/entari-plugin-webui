import axios from '@/utils/request'

export type PluginConfig = Record<string, string | number | boolean | string[] | undefined>;

export interface PluginItem {
  name: string
  id:string
  title: string
  desc: string
  version: string
  author?: string
  status: boolean  
  builtin?: boolean
  urls?: { homepage?: string }
  configurable?: boolean  
  installed: boolean
  config?: PluginConfig;
}

export interface MarketItem {
  name: string
  fullName: string
  desc: string
  author?: string
  stars: number
  updated: string
  tags: string[]
  installed: boolean
}

interface CreatePluginParams {
  name: string
}

export const listPlugins = (): Promise<PluginItem[]> => 
  axios.get('/plugins')

export const togglePluginAPI = (id: string, enable: boolean) =>
  axios.post('/plugins/toggle', { id, enable })

export const createPlugin = (params: CreatePluginParams): Promise<void> =>
  axios.post('/plugins', params)

export const installPlugin = (name: string) =>
  axios.post(`/plugins/install`, { name })

export const uninstallPlugin = (name: string) =>
  axios.post('/plugins/uninstall', { name });

export const listMarketPlugins = (): Promise<MarketItem[]> =>
  axios.get('/market/plugins');

export const searchPlugins = (keyword: string): Promise<PluginItem[]> =>
  axios.get(`/plugins/search?q=${keyword}`)
export const loadPlugin = (name: string) =>
  axios.post(`/plugins/load`, { name })
export const unloadPlugin = (name: string) =>
  axios.post(`/plugins/unload`, { name })
export const reloadPlugin = (name: string) =>
  axios.post(`/plugins/reload`, { name })
export const savePlugin = (data: Partial<PluginItem>) =>
  axios.post('/plugins/save', data)

