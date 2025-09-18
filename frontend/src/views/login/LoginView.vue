<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus';
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { login } from '@/api/users';

const form = ref({
  name: "",
  password: "",
});

const formRef = ref<FormInstance>();
const router = useRouter();
const route = useRoute();
const isLoading = ref(false);
const auth = useAuthStore();

const rules = ref<FormRules>({
  name: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '密码不能为空', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符之间', trigger: 'blur' }
  ]
});

const onSubmit = async () => {
  isLoading.value = true;
  try {
    await formRef.value?.validate();

    const res = await login(form.value);
    console.log(res);
    if (!res.success) {
      throw new Error(res.message || '登录失败');
    }
    else {
      auth.setAuthData(
        res.token,
        res.user,
        res.instances || []
      );
    }

    ElMessage.success('登录成功');
    router.push((route.query.redirect as string) || '/');

  } catch (err) {
    console.error(err);
    ElMessage.error(err instanceof Error ? err.message : '登录失败，请检查网络连接或重试');
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="login">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="120" label-position="top" size="large">
      <div href="/" class="logo">
        <img src="@/assets/Arclet-logo.jpg" alt="" />
        <div>
          <h2>Entari 可视化平台</h2>
          <p>欢迎使用</p>
        </div>
      </div>
      <el-form-item label="用户名" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="onSubmit" :loading="isLoading">登录</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style lang="scss" scoped>
.login {
  background-color: #ffffff;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;

  .el-form {
    width: 450px;
    height: 500px;
    background-color: white;
    padding: 30px;
    border-radius: 10px;
    border: 1px outset #a9a9a9;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);

    .el-form-item {
      margin-top: 20px;
    }

    .logo {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 60px;
      text-decoration: none;
      color: black;
      gap: 12px;
      margin-top: 50px;
      margin-bottom: 50px;

      img {
        width: 120px;
        height: 120px;
      }

      h2 {
        color: #2165BE;
        font-size: 28px;
      }
    }
  }

  .el-button {
    width: 100%;
    margin-top: 30px;
  }

  .el-input {
    width: 100%;
    height: 50px;
  }
}
</style>
