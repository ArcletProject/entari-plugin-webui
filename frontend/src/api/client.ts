import axios from "axios";
import router from "@/router";

const client = axios.create({
  baseURL: "",
  withCredentials: true,
  headers: { "X-Requested-With": "XMLHttpRequest" },
  timeout: 15000,
});

client.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      router.push("/login").catch(() => {});
    }
    return Promise.reject(err);
  },
);

export default client;
