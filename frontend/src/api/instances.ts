import request from '@/utils/request'

export interface InstanceItem {
  id: number
  user_id: number
  name: string
  type: string
  host: string
  port: number
  path?: string | null
  ignoreSelfMessage: boolean
  logLevel: string
  prefix: string
  created_at: string
  filename: string
  state: string
  plugins?: string[]
  config?: Record<string, unknown>
  stats?: { cpu: number; memory: number } 
}

/** 获取实例列表 */
export const listInstances = () =>
 request.get<InstanceItem[]>('/api/instances').then(res => res.data)

/** 创建实例 */
export interface CreateInstanceDto {
  name: string
  config?: Record<string, unknown>
}
export const createInstance = (data: CreateInstanceDto) =>
  request.post('/api/instances', data)

/** 启动实例 */
export const startInstance = (id: number) =>
  request.post(`/api/instances/${id}/start`)

/** 停止实例 */
export const stopInstance = (id: number) =>
  request.post(`/api/instances/${id}/stop`)

/** 删除实例 */
export const deleteInstance = (id: number) =>
  request.delete(`/api/instances/${id}`)

/** 更新实例配置 */
export const updateInstanceConfig = (id: number, config: Record<string, unknown>) =>
  request.put(`/api/instances/${id}/config`, config)