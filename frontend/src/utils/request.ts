import axios, { type AxiosRequestHeaders } from 'axios';
import { useAuthStore } from '@/stores/auth';
import { ElMessage } from 'element-plus';

const request = axios.create({
  baseURL: '',
  timeout: 5000,
});

request.interceptors.request.use((config) => {
  config.baseURL =
    window.RUNTIME_CONFIG?.baseURL || 'http://127.0.0.1:5140/api';

  if (!config.headers) config.headers = {} as AxiosRequestHeaders;
  config.headers.Authorization = useAuthStore().token;
  return config;
});


request.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    const msg = err?.response?.data?.message || err?.message || '网络错误';
    ElMessage.error(msg);
    return Promise.reject(err);
  },
);

export default request;
