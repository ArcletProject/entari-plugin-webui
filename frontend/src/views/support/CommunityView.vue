<!-- ArcletCommunity.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

/* 项目数据 */
const projects = ref([
    { name: 'Alconna', desc: '命令解析器', url: 'https://github.com/ArcletProject/Alconna' },
    { name: 'Cithun', desc: '类文件系统的权限管理', url: 'https://github.com/ArcletProject/Cithun' },
    { name: 'Letoderea', desc: '高效事件系统', url: 'https://github.com/ArcletProject/Letoderea' },
    { name: 'Entari', desc: '基于 Satori 的跨平台 IM 框架', url: 'https://github.com/ArcletProject/Entari' },
    { name: 'Tarina', desc: '功能与开发工具集合', url: 'https://github.com/ArcletProject/Tarina' },
    { name: 'NEPattern', desc: '复杂正则匹配', url: 'https://github.com/ArcletProject/NEPattern' },
    { name: 'Alconna-Tools', desc: 'Alconna 拓展工具', url: 'https://github.com/ArcletProject/Alconna-Tools' },
    { name: 'Alconna-Graia', desc: 'Alconna 与 Graia 集成', url: 'https://github.com/ArcletProject/Alconna-Graia' },
    { name: 'nonebot-plugin-alconna', desc: 'Alconna 与 NoneBot2 集成', url: 'https://github.com/ArcletProject/nonebot-plugin-alconna' },
    { name: 'ArcletTS', desc: 'TypeScript 版本 Arclet', url: 'https://github.com/ArcletProject/ArcletTS' }
])

/* 贡献方式 */
const ways = ref([
    { icon: 'Warning', title: '提交 Issue', desc: 'Bug / 需求 / 文档改进', url: 'https://github.com/ArcletProject' },
    { icon: 'Position', title: 'Pull Request', desc: '直接提交代码与文档', url: 'https://github.com/ArcletProject' },
    { icon: 'ChatDotSquare', title: 'QQ 群讨论', desc: '群号：654490750', action: () => { navigator.clipboard.writeText('123456789'); ElMessage.success('QQ 群号已复制') } }
])

/* 跳转外链 */
function jump(url: string) {
    window.open(url, '_blank')
}
</script>

<template>
    <div class="community">
        <!-- Hero -->
        <section class="hero">
            <h1>Arclet Project · 社区支持</h1>
            <p>
                与机器人开发相关、却不局限于机器人的框架集合体。<br>
                欢迎任何形式的贡献！
            </p>
        </section>

        <!-- 项目列表 -->
        <section>
            <h2>项目一览</h2>
            <el-row :gutter="20">
                <el-col v-for="p in projects" :key="p.name" :xs="24" :sm="12" :md="8" class="project-col">
                    <el-card shadow="hover" class="project-card" @click="jump(p.url)">
                        <h3>{{ p.name }}</h3>
                        <p>{{ p.desc }}</p>
                        <el-link type="primary" :underline="false">前往 GitHub →</el-link>
                    </el-card>
                </el-col>
            </el-row>
        </section>

        <!-- 参与方式 -->
        <section>
            <h2>如何参与</h2>
            <el-row :gutter="20">
                <el-col v-for="w in ways" :key="w.title" :xs="24" :sm="8">
                    <el-card shadow="hover" class="way-card">
                        <el-icon size="32" color="#409EFF">
                            <component :is="w.icon" />
                        </el-icon>
                        <h3>{{ w.title }}</h3>
                        <p>{{ w.desc }}</p>
                        <el-button :type="w.url ? 'primary' : 'default'" text
                            @click="w.url ? jump(w.url) : w.action?.()">
                            {{ w.title === 'QQ 群讨论' ? '复制群号' : '立即前往' }}
                        </el-button>
                    </el-card>
                </el-col>
            </el-row>
        </section>

        <!-- Footer -->
        <footer>
            <p>
                上次更新：2025/9/5 12:22
            </p>
        </footer>
    </div>
</template>

<style scoped>
.community {
    max-width: 1200px;
    margin: 0 auto;
    padding: 64px 20px 40px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.hero {
    text-align: center;
    margin-bottom: 60px;
}

.hero h1 {
    font-size: 36px;
    margin: 0 0 12px;
}

.hero p {
    font-size: 18px;
    color: #666;
    line-height: 1.6;
}

section {
    margin-bottom: 60px;
}

section h2 {
    font-size: 28px;
    margin-bottom: 24px;
}

.project-card,
.way-card {
    cursor: pointer;
    border-radius: 12px;
    transition: transform 0.2s;
    height: 100%;
}

.project-card:hover,
.way-card:hover {
    transform: translateY(-4px);
}

.project-card h3 {
    margin: 0 0 8px;
    font-size: 18px;
}

.project-card p {
    font-size: 14px;
    color: #555;
    margin-bottom: 8px;
}

.way-card {
    text-align: center;
}

.way-card h3 {
    margin: 12px 0 8px;
    font-size: 18px;
}

.way-card p {
    font-size: 14px;
    color: #666;
    margin-bottom: 12px;
}

footer {
    text-align: center;
    font-size: 14px;
    color: #999;
}
</style>