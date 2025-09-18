<!-- EntariLanding.vue -->
<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
    // 可以在这里埋点 / 请求版本号
})
</script>

<template>
    <div class="landing">

        <section class="hero">
            <h1 class="title">
                Entari <span class="sub">Plugin WebUI</span>
            </h1>
            <p class="subtitle">
                基于 Satori 协议的即时通信开发框架，<br>
                零门槛图形化环境搭建、插件管理、配置编辑与热重载。
            </p>
            <div class="actions">
                <el-button type="primary" size="large" @click="$router.push('/dashboard')">
                    立即体验
                </el-button>
                <el-button size="large" tag="a" href="https://entari.arclet.io" target="_blank">
                    阅读文档
                </el-button>
            </div>
        </section>

        <section class="features">
            <h2>特性一览</h2>
            <el-row :gutter="32">
                <el-col :xs="24" :sm="12" :md="6" class="feature">
                    <el-icon size="48" color="#409EFF">
                        <Setting />
                    </el-icon>
                    <h3>图形化配置</h3>
                    <p>一键编辑 .env / yml / json，实时热重载，无需重启。</p>
                </el-col>

                <el-col :xs="24" :sm="12" :md="6" class="feature">
                    <el-icon size="48" color="#67C23A">
                        <Grid />
                    </el-icon>
                    <h3>插件市场</h3>
                    <p>浏览、安装、更新、卸载插件，支持版本冲突检测与回滚。</p>
                </el-col>

                <el-col :xs="24" :sm="12" :md="6" class="feature">
                    <el-icon size="48" color="#E6A23C">
                        <Timer />
                    </el-icon>
                    <h3>定时任务</h3>
                    <p>内置 CRON 表达式可视化编辑器，秒级热生效。</p>
                </el-col>

                <el-col :xs="24" :sm="12" :md="6" class="feature">
                    <el-icon size="48" color="#F56C6C">
                        <Lightning />
                    </el-icon>
                    <h3>异步并发</h3>
                    <p>基于 AnyIO，支持高并发事件循环，插件零成本异步。</p>
                </el-col>
            </el-row>
        </section>

        <!-- 流程 -->
        <section class="workflow">
            <h2>三步上手</h2>
            <el-timeline>
                <el-timeline-item timestamp="第 1 步" placement="top">
                    <el-card>
                        <h4>创建项目</h4>
                        <p>填写名称、选择模板，30 秒即可初始化完毕。</p>
                    </el-card>
                </el-timeline-item>
                <el-timeline-item timestamp="第 2 步" placement="top">
                    <el-card>
                        <h4>安装插件</h4>
                        <p>在插件市场一键安装需要的功能模块，自动处理依赖。</p>
                    </el-card>
                </el-timeline-item>
                <el-timeline-item timestamp="第 3 步" placement="top">
                    <el-card>
                        <h4>启动 & 调试</h4>
                        <p>点击「运行」按钮，实时查看日志与消息收发，支持断点调试。</p>
                    </el-card>
                </el-timeline-item>
            </el-timeline>
        </section>

        <section class="cta">
            <h2>准备好开始了吗？</h2>
            <el-button type="primary" size="large" @click="$router.push('/')">
                打开面板
            </el-button>
        </section>

        <footer class="footer">
            <p>
                © 2025 ArcletProject ·
                <a href="https://github.com/ArcletProject/Entari" target="_blank">GitHub</a>
            </p>
        </footer>
    </div>
</template>

<style scoped>
.landing {
    padding: 80px 24px 40px;
    max-width: 1100px;
    margin: 0 auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--landing-bg);
}

.hero {
    text-align: center;
    margin-bottom: 80px;
}

.title {
    font-size: 48px;
    font-weight: 700;
    color: var(--landing-title);
    margin: 0 0 8px;
    transition: color 0.3s;
}

.title .sub {
    font-weight: 400;
    color: var(--landing-sub-highlight);
    transition: color 0.3s;
}

.subtitle {
    font-size: 20px;
    color: var(--landing-subtitle);
    line-height: 1.5;
    margin-bottom: 32px;
    transition: color 0.3s;
}

.actions .el-button {
    margin: 0 8px;
}

.features,
.workflow,
.cta {
    margin-bottom: 80px;
}

.features h2,
.workflow h2,
.cta h2 {
    text-align: center;
    margin-bottom: 40px;
    font-size: 32px;
    color: var(--landing-title);
    transition: color 0.3s;
}

.feature {
    text-align: center;
    padding: 0 12px;
}

.feature h3 {
    margin: 16px 0 8px;
    font-size: 18px;
    color: var(--landing-feature-title);
    transition: color 0.3s;
}

.feature p {
    font-size: 14px;
    color: var(--landing-feature-desc);
    transition: color 0.3s;
}

.workflow {
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
}

:deep(.el-timeline-item__wrapper) {
    background: var(--landing-timeline-bg);
    border: 1px solid var(--landing-timeline-border);
    border-radius: 8px;
    padding: 16px;
}

:deep(.el-timeline-item__timestamp) {
    color: var(--landing-sub-highlight);
}

:deep(.el-card) {
    background: var(--landing-timeline-bg);
    color: var(--landing-timeline-title);
    border: none;
}

:deep(.el-card__body h4) {
    color: var(--landing-timeline-title);
    margin: 0 0 8px;
}

:deep(.el-card__body p) {
    color: var(--landing-timeline-desc);
    margin: 0;
}

.cta {
    text-align: center;
}

.footer {
    text-align: center;
    font-size: 14px;
    color: var(--landing-footer);
    transition: color 0.3s;
}

.footer a {
    color: var(--landing-link);
    text-decoration: none;
    transition: color 0.3s;
}

:deep(.el-button--primary) {
    background: var(--landing-btn-primary-bg);
    border-color: var(--landing-btn-primary-bg);
    color: var(--landing-btn-primary-text);
}

:deep(.el-button--primary:hover) {
    background: var(--landing-btn-primary-hover-bg, #5fa7ff);
    border-color: var(--landing-btn-primary-hover-bg, #5fa7ff);
}

:deep(.el-button.is-plain) {
    background: var(--landing-btn-plain-bg);
    border-color: var(--landing-btn-plain-border);
    color: var(--landing-btn-plain-text);
}

:deep(.el-button.is-plain:hover) {
    border-color: var(--landing-btn-primary-bg);
    color: var(--landing-btn-primary-bg);
}

@media (max-width: 768px) {
    .title {
        font-size: 36px;
    }
}
</style>