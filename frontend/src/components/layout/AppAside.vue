<script setup lang="ts">
import { isCollapse } from './isCollapse';
</script>

<template>
    <el-aside :class="['sidebar', { 'sidebar--collapse': isCollapse }]">
        <el-scrollbar>

            <el-menu router unique-opened default-active="1" :collapse="isCollapse" class="custom-aside-menu">
                <a href="/" class="logo">
                    <img src="@/assets/Arclet-logo.jpg" alt="" />
                    <h1>Entari</h1>
                </a>

                <el-menu-item index="/">
                    <el-icon>
                        <IEpHomeFilled />
                    </el-icon>
                    <span>首页</span>
                </el-menu-item>

                <el-menu-item index="/plugin">
                    <el-icon>
                        <IEpShop />
                    </el-icon>
                    <span>插件管理</span>
                </el-menu-item>

                <el-menu-item index="/menus">
                    <el-icon>
                        <IEpPrinter />
                    </el-icon>
                    <span>实例管理</span>
                </el-menu-item>

                <el-menu-item index="/control">
                    <el-icon>
                        <IEpPostcard />
                    </el-icon>
                    <span>控制台</span>
                </el-menu-item>

                <el-menu-item index="/set">
                    <el-icon>
                        <IEpTools />
                    </el-icon>
                    <span>配置管理</span>
                </el-menu-item>

                <el-menu-item index="/plugin-market">
                    <el-icon>
                        <IEpSchool />
                    </el-icon>
                    <span>插件市场</span>
                </el-menu-item>

                <el-sub-menu index="7">
                    <template #title>
                        <el-icon>
                            <IEpPromotion />
                        </el-icon>
                        <span>帮助与支持</span>
                    </template>
                    <el-menu-item index="7-1" route="/support/docs">
                        <el-icon>
                            <IEpReading />
                        </el-icon>
                        <span>文档</span>
                    </el-menu-item>
                    <el-menu-item index="7-2" route="/support/community">
                        <el-icon>
                            <IEpMenu />
                        </el-icon>
                        <span>社区支持</span>
                    </el-menu-item>
                </el-sub-menu>

                <el-sub-menu index="8">
                    <template #title>
                        <el-icon>
                            <IEpInfoFilled />
                        </el-icon>
                        <span>关于</span>
                    </template>
                    <el-menu-item index="/about/project-info">
                        <el-icon>
                            <IEpPieChart />
                        </el-icon>
                        <span>项目信息</span>
                    </el-menu-item>
                    <el-menu-item index="/about/contributors">
                        <el-icon>
                            <IEpUserFilled />
                        </el-icon>
                        <span>贡献者</span>
                    </el-menu-item>
                </el-sub-menu>
            </el-menu>

        </el-scrollbar>
    </el-aside>
</template>

<style lang="scss" scoped>
.el-aside {
    width: 250px;
    height: 100vh;
    background-color: var(--el-bg);
    color: var(--el-text);
    transition: width 0.7s;
    opacity: 0.8;
}

.sidebar {
    width: 250px;
    transition: width 0.7s;

    &.sidebar--collapse {
        width: 60px;
    }
}

.el-menu {
    width: 100%;
    background-color: transparent;
    border-right: none;
    padding-left: 20px;
    padding-right: 20px;

    &.el-menu--collapse {
        & h1 {
            display: none;
            transition: display 0.1s;
        }

        width: 60px;
        transition: width 0.1s;
        padding: 0;
    }

    .el-menu-item {
        color: var(--el-text);
    }
}

.logo {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 60px;
    text-decoration: none;
    color: var(--el-text);
    border-bottom: 1px solid #4E86D1;
    padding-bottom: 8px;
    margin-bottom: 8px;

    img {
        width: 50px;
        height: 50px;
    }

    h1 {
        font-size: 20px;
        margin: 0 0 0 8px;
    }
}
</style>