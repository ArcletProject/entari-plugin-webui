<script setup lang="ts">

const contributors = ref([
    { login: 'RF-Tar-Railt', avatar_url: 'https://avatars.githubusercontent.com/u/42648639?v=4' },
    { login: 'qxjq', avatar_url: 'https://avatars.githubusercontent.com/u/153436697?s=96&v=4' }
])
</script>

<template>
    <div class="home">
        <section class="hero">
            <h1 class="title">Entari Plugin WebUI</h1>
            <p class="subtitle">A project out of interests and loves</p>

            <div class="actions">
                <el-button type="primary" size="large" tag="a"
                    href="https://github.com/ArcletProject/entari-plugin-webui" target="_blank">
                    <el-icon>
                        <IEpStarFilled />
                    </el-icon> Star 这个项目！
                </el-button>
                <el-button plain size="large" tag="a" href="https://github.com/ArcletProject/entari-plugin-webui/issues"
                    target="_blank">
                    提交 Issue
                </el-button>
            </div>
        </section>

        <section class="contributors">
            <h2 class="section-title">
                Active Contributors
                <small>07-1 - 07-16</small>
            </h2>

            <p class="desc">
                本项目由众多开源社区成员共同维护。<br />
                感谢每一位贡献者的付出！
            </p>

            <div class="avatar-list">
                <a v-for="c in contributors" :key="c.login" :href="`https://github.com/${c.login}`" target="_blank">
                    <el-avatar :src="c.avatar_url" :size="60" />
                    <span class="login">{{ c.login }}</span>
                </a>
            </div>

            <el-button plain round class="more-btn">
                查看 Entari Plugin WebUI 贡献者
            </el-button>
        </section>
    </div>
</template>

<style scoped>
.home {
    padding: 60px 24px;
    max-width: 900px;
    margin: 0 auto;
    text-align: center;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--about-page-bg);
}

.hero {
    margin-bottom: 80px;
}

.title {
    font-size: 48px;
    font-weight: 700;
    margin: 0 0 8px;
    color: var(--about-title);
}

.subtitle {
    font-size: 20px;
    color: var(--about-subtitle);
    margin-bottom: 32px;
}

.actions .el-button {
    margin: 0 8px;
    font-size: 16px;
}

/* Contributors */
.section-title {
    font-size: 28px;
    font-weight: 600;
    margin-bottom: 8px;
    color: var(--about-section-title);
    transition: color 0.3s;
}

.section-title small {
    font-size: 14px;
    color: var(--about-section-small);
    margin-left: 12px;
    transition: color 0.3s;
}

.desc {
    color: var(--about-desc);
    line-height: 1.7;
    margin-bottom: 32px;
    transition: color 0.3s;
}

.avatar-list {
    display: flex;
    justify-content: center;
    gap: 32px;
    flex-wrap: wrap;
    margin-bottom: 36px;
}

.avatar-list a {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-decoration: none;
}

.login {
    margin-top: 8px;
    font-size: 14px;
    color: var(--about-login);
    transition: color 0.3s;
}

.more-btn {
    font-size: 15px;
}

:deep(.el-button--primary) {
    background: var(--about-btn-primary-bg);
    border-color: var(--about-btn-primary-bg);
    color: var(--about-btn-primary-text);
}

:deep(.el-button--primary:hover) {
    background: var(--about-btn-primary-hover-bg, #5fa7ff);
    border-color: var(--about-btn-primary-hover-bg, #5fa7ff);
}

:deep(.el-button.is-plain) {
    border-color: var(--about-btn-plain-border);
    color: var(--about-btn-plain-text);
    transition: border-color 0.3s, color 0.3s;
}

:deep(.el-button.is-plain:hover) {
    border-color: var(--about-btn-primary-bg);
    color: var(--about-btn-primary-bg);
}

:deep(.el-avatar) {
    transition: box-shadow 0.3s;
}

:deep(.el-avatar:hover) {
    box-shadow: 0 0 0 3px var(--about-avatar-ring);
}
</style>