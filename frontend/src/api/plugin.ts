import axios from '@/utils/request'

export interface PluginItem {
  name: string
  version: string
  desc: string
  status: 'loaded' | 'unloaded'
  entry?: string
  code?: string
}

interface CreatePluginParams {
  name: string
}

export const listPlugins = (): Promise<PluginItem[]> => axios.get('/plugins')
export const searchPlugins = (keyword: string): Promise<PluginItem[]> =>
  axios.get(`/plugins/search?q=${keyword}`)
export const installPlugin = (name: string) =>
  axios.post(`/plugins/install`, { name })
export const loadPlugin = (name: string) =>
  axios.post(`/plugins/load`, { name })
export const unloadPlugin = (name: string) =>
  axios.post(`/plugins/unload`, { name })
export const reloadPlugin = (name: string) =>
  axios.post(`/plugins/reload`, { name })
export const savePlugin = (data: Partial<PluginItem>) =>
  axios.post('/plugins/save', data)

export const createPlugin = (params: CreatePluginParams): Promise<void> =>
  axios.post('/plugins', params)