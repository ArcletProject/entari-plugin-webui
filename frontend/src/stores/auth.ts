import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface UserInfo {
  name: string;
  email: string;
}

export interface Instance {
  id: number                    // 后端主键，int
  user_id?: number              // 所属用户 id
  name: string                  // 实例名称
  type: string                 // 连接类型：ws / http / reverse-ws ...
  host: string                 // 监听地址
  port: number                 // 监听端口
  path?: string | null         // 路径
  ignoreSelfMessage?: boolean  // 是否忽略自身消息
  logLevel?: string            // 日志等级
  prefix?: string              // 命令前缀
  created_at?: string          // 创建时间
  filename?: string             // *.yml 文件名
  state?: string               // 运行状态
  plugins?: string[]              // 已启用插件列表
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref('');
  const user = ref<UserInfo | null>(null);
  const instances = ref<Instance[]>([]);

  /* 登录成功时调用一次 */
  function setAuthData(t: string, u: UserInfo, list: Instance[] = []) {
    token.value = t;
    user.value = u;
    instances.value = list;
  }

  /* 退出登录 */
  function logout() {
    token.value = '';
    user.value = null;
    instances.value = [];
  }

  // 设置实例列表
  function setInstances(list: Instance[]) {
    instances.value = list;
  }

  // 添加或更新单个实例
  function addInstance(ins: Partial<Instance>) {
      const idx = instances.value.findIndex(i => i.id === ins.id)
      // 用后端返回的数据补全默认值
      const merged: Instance = {
        id: ins.id!,
        name: ins.name!,
        type: ins.type!,
        host: ins.host!,
        port: ins.port!,
        path: ins.path ?? '',
        ignoreSelfMessage: ins.ignoreSelfMessage ?? true,
        logLevel: ins.logLevel ?? 'INFO',
        prefix: ins.prefix ?? '/',
        created_at: ins.created_at ?? new Date().toISOString(),
        filename: ins.filename!,
        state: ins.state ?? '已停止',
        plugins: ins.plugins ?? [],
        ...ins,
      }

      if (idx >= 0) {
        instances.value[idx] = merged
      } else {
        instances.value.push(merged)
      }
    }

  return { 
    token, 
    user, 
    instances, 
    setAuthData, 
    logout,
    setInstances,
    addInstance
  };
}, {
  persist: {
    storage: localStorage,
    pick: ['token', 'user', 'instances'],
  },
});