import axios from '@/utils/request'

interface CommandsPlugin {
  need_notice_me: boolean
  need_reply_me: boolean
  use_config_prefix: boolean
}
interface RecordMessagePlugin {
  record_send: boolean
}
interface AutoReloadPlugin {
  watch_dirs: string
  watch_config: boolean
}
interface HelpPlugin {
  help_command: string
  help_alias: string
  page_size: number
}
interface DatabasePlugin {
  type: string
  name: string
  driver: string
}
interface ServerAdapter {
  $path: string
  uin: number
  sign_url: string
  protocol: string
  log_level: string
  use_png: boolean
}
interface ServerPlugin {
  host: string
  port: number
  adapters: ServerAdapter[]
}
// 总插件类型
export interface Plugins {
  $files?: string
  $prelude?: string
  record_message: RecordMessagePlugin
  auto_reload: AutoReloadPlugin
  echo: Record<string, unknown> 
  commands: CommandsPlugin
  help: HelpPlugin
  database: DatabasePlugin
  server: ServerPlugin
  webui: Record<string, unknown>
  [key: string]: unknown 
}

export interface Config {
    basic: {
        network: {
        type: string
        host: string
        port: number
        path?: string
        token?: string
        }[]
        ignore_self_message: boolean
        log: {
        level: string
        ignores?: string[]
        save?: {
            enable: boolean
            rotation?: string
            compression?: string
            colorize?: boolean
        }
        }
        prefix: string[]
        skip_req_missing?: boolean
        cmd_count?: number
        external_dirs?: string[]
    }
    plugins: Plugins
}

export const getConfig = (): Promise<Config> =>
  axios.get('/config').then(res => res.data)

export const saveConfig = (cfg: Config): Promise<{ success: true }> =>
  axios.post('/config', cfg).then(res => res.data)
