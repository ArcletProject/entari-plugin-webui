<template>
  <n-message-provider>
    <n-dialog-provider>
      <n-notification-provider>
        <NuxtLayout>
          <NuxtPage />
        </NuxtLayout>
      </n-notification-provider>
    </n-dialog-provider>
  </n-message-provider>
</template>

<script setup lang="ts">
// 应用入口
</script>

<style>
/* 全局样式 */
html, body, #__nuxt {
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
