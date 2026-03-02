<template>
  <NuxtLayout name="blank">
    <n-card class="login-card" title="Entari WebUI">
      <template #header-extra>
        <n-button quaternary circle @click="toggleColorMode">
          <template #icon>
            <Icon :name="colorMode.value === 'dark' ? 'mdi:weather-sunny' : 'mdi:weather-night'" />
          </template>
        </n-button>
      </template>

      <n-form ref="formRef" :model="form" :rules="rules">
        <n-form-item label="管理员密码" path="password">
          <n-input
            v-model:value="form.password"
            type="password"
            show-password-on="click"
            placeholder="请输入管理员密码"
            @keyup.enter="handleLogin"
          />
        </n-form-item>

        <n-button
          type="primary"
          block
          :loading="loading"
          @click="handleLogin"
        >
          登录
        </n-button>
      </n-form>

      <template #footer>
        <n-text depth="3">
          Entari WebUI v0.2.0
        </n-text>
      </template>
    </n-card>
  </NuxtLayout>
</template>

<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'

definePageMeta({
  layout: false,
})

const router = useRouter()
const colorMode = useColorMode()
const auth = useAuth()
const message = useMessage()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const form = reactive({
  password: '',
})

const rules: FormRules = {
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
  ],
}

const toggleColorMode = () => {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}

const handleLogin = async () => {
  // 验证表单
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    const result = await auth.login(form.password)

    if (result.success) {
      message.success('登录成功')
      router.push('/')
    } else {
      message.error(result.message || '登录失败')
    }
  } catch (e) {
    message.error('网络错误')
  } finally {
    loading.value = false
  }
}

// 检查是否本地模式
onMounted(async () => {
  await auth.init()

  // 本地模式自动跳转
  if (auth.localMode.value) {
    router.push('/')
    return
  }

  // 已认证自动跳转
  if (auth.isAuthenticated.value) {
    router.push('/')
  }
})
</script>

<style scoped>
.login-card {
  width: 400px;
  max-width: 90vw;
}
</style>
