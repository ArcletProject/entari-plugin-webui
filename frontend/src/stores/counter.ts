import { defineStore } from 'pinia'
import axios from 'axios'

export const useInitData = defineStore('webInitData', {
  state: () => ({
    name: '',
    today_messages: 0,  
    weekLabels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    weekMessages: [0, 0, 0, 0, 0, 0, 0], 
    message_count: 0,
    plugin_enabled: 0,
    plugin_total: 0,
    runtime: 0
  }),

  actions: {
    async fetchInitData() {
      const { data } = await axios.get('/init_data')
      Object.assign(this, data)
    }
  }
})