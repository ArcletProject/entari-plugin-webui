<template><el-button text @click="theme.toggle()"><el-icon><Sunny v-if="theme.mode==='light'"/><Moon v-else/></el-icon></el-button></template>
<script setup lang="ts">import { Sunny, Moon } from "@element-plus/icons-vue"; import { useThemeStore } from "@/stores/theme"; const theme = useThemeStore();</script>
