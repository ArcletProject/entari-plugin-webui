import { defineStore } from "pinia";
import { ref } from "vue";
import api from "@/api/client";

export interface MenuItem { label_key: string; icon: string; path: string; order: number; label?: string; }

export const useMenuStore = defineStore("menu", () => {
  const items = ref<MenuItem[]>([]);
  async function load() {
    const r = await api.get("/api/menus");
    items.value = r.data.menus;
  }
  return { items, load };
});
