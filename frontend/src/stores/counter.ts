import { defineStore } from 'pinia'

export const useInitData = defineStore('webInitData', {
    state: () => ({
      name: "",
      message_count: 0,
      instance_count: 0,
      runtime: 0,
      memory_usage: 0,
    })
});


