<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useDark, useToggle } from '@vueuse/core'

const isDark = useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
})

const toggleDark = useToggle(isDark)
provide('isDark', isDark)
provide('toggleDark', toggleDark)
</script>

<template>
  <RouterView />
</template>

<style scoped></style>