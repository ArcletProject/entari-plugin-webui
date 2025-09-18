import axios from 'axios';
import { ElMessage } from 'element-plus';

export default async function initRuntime() {
  let base = 'http://127.0.0.1:5140/api';
  
    try {
      const res = await fetch(`/frontend/runtime.json?${Date.now()}`);
      if (res.ok) {
        const { baseURL } = await res.json();
        base = baseURL;
        const cacheKey = 'srv_base';
        localStorage.setItem(cacheKey, base);
      } else {
        ElMessage.warning('runtime.json 拉取失败，使用默认 baseURL');
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      ElMessage.error(`拉取配置失败：${msg}`);
    }

  window.RUNTIME_CONFIG = { baseURL: base };
  axios.defaults.baseURL = base;
}