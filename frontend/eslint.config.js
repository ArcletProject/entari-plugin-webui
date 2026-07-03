import pluginVue from 'eslint-plugin-vue'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'

export default defineConfigWithVueTs(
  ...vueTsConfigs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    name: 'app',
    rules: {
      'vue/multi-word-component-names': 'off',
    }
  },
)
