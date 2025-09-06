<script setup lang="ts">
import AppAside from './AppAside.vue'
import AppHeader from './AppHeader.vue'
</script>

<template>
    <div class="common-layout">
        <el-container>
            <AppAside />
            <el-container class="header-and-main">
                <AppHeader />
                <el-main class="main-wrapper">
                    <div class="scroll-container">
                        <RouterView />
                    </div>
                </el-main>
            </el-container>
        </el-container>
    </div>
</template>

<style lang="scss" scoped>
.main-wrapper {
    flex: 1;
    overflow: hidden;
    background-color: var(--main-bg);
    color: var(--main-text);
    transition: background-color 0.3s, color 0.3s;
}

.scroll-container {
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 8px;
    margin: 0 -20px;

    &::-webkit-scrollbar {
        width: 8px;
    }

    &::-webkit-scrollbar-thumb {
        background: var(--scroll-thumb);
        border-radius: 4px;
    }

    &::-webkit-scrollbar-track {
        background: var(--scroll-track);
    }
}

.header-and-main {
    flex-direction: column;
    height: 100vh;
}

.el-main {
    padding: 0;
    margin: 0;
    background-color: var(--main-bg);
}
</style>
