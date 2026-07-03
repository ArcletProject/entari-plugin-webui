<template>
  <div class="login-card">
    <h2>{{ t("auth.login") }}</h2>
    <el-form
      v-loading="loading"
      @submit.prevent="onSubmit"
    >
      <el-form-item
        v-if="!auth.localMode"
        :label="t('auth.password')"
      >
        <el-input
          v-model="password"
          type="password"
          show-password
          @keyup.enter="onSubmit"
        />
      </el-form-item>
      <el-button
        type="primary"
        :loading="loading"
        @click="onSubmit"
      >
        {{ t("auth.submit") }}
      </el-button>
    </el-form>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useI18n } from "vue-i18n";
import { useAuthStore } from "@/stores/auth";
const auth = useAuthStore();
const router = useRouter();
const { t } = useI18n();
const password = ref("");
const loading = ref(false);
onMounted(async () => { await auth.init(); if (auth.localMode) router.replace("/"); });
async function onSubmit() {
  loading.value = true;
  try { await auth.login(password.value); router.replace("/"); }
  catch (e: unknown) {
    const err = e as { response?: { status: number }; message: string };
    const status = err.response?.status;
    ElMessage.error(status === 429 ? t("auth.rate_limited") : status === 401 ? t("auth.wrong_password") : err.message);
  } finally { loading.value = false; }
}
</script>
<style scoped>.login-card{width:320px;padding:24px;background:var(--el-bg-color);border-radius:8px;box-shadow:var(--el-box-shadow-light);}</style>
