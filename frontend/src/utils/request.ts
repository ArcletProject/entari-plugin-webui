import axios, { type AxiosRequestHeaders } from 'axios';
import { useAuthStore } from '@/stores/auth';
import { ElMessage } from 'element-plus';

const getBaseURL = () =>
  window.RUNTIME_CONFIG?.baseURL || 'http://127.0.0.1:5140/api';
  // console.log('Base URL:', getBaseURL());

const request = axios.create({
  baseURL: getBaseURL(),
  timeout: 5000,
});

//请求拦截器
request.interceptors.request.use((config)=> {
  if (!config.headers) {
    config.headers = {} as AxiosRequestHeaders;
  }
  const store = useAuthStore();
  config.headers.Authorization = store.token;
  return config;
})


request.interceptors.response.use(
  (resp) => resp.data, 
  (err) => {
    const msg = err?.response?.data?.message || err?.message || '网络错误';
    ElMessage.error(msg);
    return Promise.reject(err);
  },
);

export default request;