// src/stores/usePluginStore.ts
import { ref } from 'vue'
import { listPlugins, } from '@/api/plugin'
import type { PluginItem } from '@/api/plugin'

export interface Plugin {
  name: string
  fullName: string
  desc: string
  author?: string
  stars: number
  updated: string
  tags: string[]
  installed: boolean
}

export const pluginStore = ref<Plugin[]>([])

export async function loadPluginList() {
  const raw = await listPlugins()
  pluginStore.value = raw.map((p: PluginItem) => ({
    name: p.id,
    fullName: p.title,
    desc: p.desc,
    author: p.author,
    stars: 0,
    updated: '',
    tags: [],
    installed: p.installed,
  }))
}