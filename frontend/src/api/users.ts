import axios from '@/utils/request';
import { useAuthStore } from '@/stores/auth';

export interface LoginInfo {
  name: string;
  password: string;
}

export interface Instance {
    id: number        
    name: string
    type: string
    host: string
    port: number
    state: string
    path?: string
}

export interface LoginResult {
  success: boolean;
  message: string;
  token: string;
  instances?: Instance[];
  user: { name: string; email: string };
}

// 获取用户信息
export interface UserInfo {
  success: boolean;
  message: string;
  state: number;
  token: string;
  name: string;
}

export const login = (data: LoginInfo): Promise<LoginResult> =>
  axios.post('/login', data);

export const logout = (): Promise<boolean> =>
  axios.post('/logout');

export const updateUser = (data: { password?: string; email?: string }): Promise<{
  success: boolean;
  message: string;
}> => {
  const authStore = useAuthStore();
  return axios.post('/user/update', data, {
    headers: { Authorization: authStore.token },
  });
};