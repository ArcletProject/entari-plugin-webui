// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  // SPA 模式
  ssr: false,

  // 模块
  modules: [
    '@bg-dev/nuxt-naiveui',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxtjs/color-mode',
    'nuxt-icon',
  ],

  // 应用配置
  app: {
    head: {
      title: 'Entari WebUI',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Entari 可视化管理面板' },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
      ],
    },
  },

  // 运行时配置
  runtimeConfig: {
    public: {
      apiBase: '/api',
      wsBase: '/ws',
    },
  },

  // 颜色模式
  colorMode: {
    classSuffix: '',
    preference: 'system',
    fallback: 'light',
  },

  // Naive UI 配置
  naiveui: {
    colorModePreference: 'system',
  },

  // 构建配置
  nitro: {
    output: {
      publicDir: '../src/entari_plugin_webui/frontend',
    },
  },

  // TypeScript 配置
  typescript: {
    strict: true,
  },

  // Vite 配置
  vite: {
    optimizeDeps: {
      include: ['echarts', 'vue-echarts'],
    },
    // 开发模式代理（连接后端 API）
    // server: {
    //   proxy: {
    //     '/api': {
    //       target: 'http://127.0.0.1:9555',
    //       changeOrigin: true,
    //     },
    //     '/ws': {
    //       target: 'ws://127.0.0.1:9555',
    //       ws: true,
    //     },
    //   },
    // },
  },
})
