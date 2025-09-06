<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { saveConfig, type Config, type Plugins } from '@/api/set'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { cloneDeep } from 'lodash-es'

// 前端额外维护的「启用」标记
const pluginEnable = reactive({
    record_message: true,
    scheduler: true,
    echo: true,
    inspect: true,
    auto_reload: true,
    commands: true,
    help: true,
})

// 配置表单
const settings = reactive<Config>({
    basic: {
        network: [
            {
                type: 'ws',
                host: '127.0.0.1',
                port: 7777,
                token: '35c65152638a93de',
            },
        ],
        ignore_self_message: true,
        log: {
            level: 'INFO',
            ignores: [],
            save: {
                enable: false,
                rotation: '00:00',
                compression: 'zip',
                colorize: false,
            },
        },
        prefix: ['/'],
        skip_req_missing: false,
        cmd_count: 4096,
        external_dirs: [],
    },
    plugins: {
        $files: '',
        $prelude: '',
        record_message: { record_send: true },
        auto_reload: { watch_dirs: '', watch_config: true },
        echo: {},
        commands: {
            need_notice_me: true,
            need_reply_me: false,
            use_config_prefix: true,
        },
        help: {
            help_command: 'help',
            help_alias: '帮助,命令帮助',
            page_size: 10,
        },
        database: { type: 'sqlite', name: 'database.db', driver: 'aiosqlite' },
        server: {
            host: '127.0.0.1',
            port: 5140,
            adapters: [
                {
                    $path: 'nekobox.main:NekoBoxAdapter',
                    uin: 2507078797,
                    sign_url: 'https://sign.lagrangecore.org/api/sign/30366',
                    protocol: 'remote',
                    log_level: 'INFO',
                    use_png: false,
                },
            ],
        },
        webui: {},
    },
})

onMounted(async () => {
    try {
        // 这里直接用 axios 绕过拦截器（不绕过有bug，暂时不改）
        const cfg = await axios.get<Config>(window.RUNTIME_CONFIG?.baseURL + '/config')

        Object.assign(settings, cloneDeep(cfg))
    } catch (error) {
        ElMessage.error('加载配置失败，请检查后端服务是否正常')
        console.error('加载配置失败', error)
    }
})

const save = async () => {
    // 深拷贝
    const src = JSON.parse(JSON.stringify(settings))
    src.plugins.server.adapters.forEach((a: { sign_url?: string }) => {
        if (a.sign_url) a.sign_url = a.sign_url.trim()
    })

    // 最小化配置
    const minimal: Config = {
        basic: {
            network: src.basic.network,
            ignore_self_message: src.basic.ignore_self_message,
            prefix: src.basic.prefix,
            log: { level: src.basic.log.level },
        },
        plugins: {} as Plugins,
    }
    if (src.basic.log.ignores?.length) minimal.basic.log.ignores = src.basic.log.ignores
    if (src.basic.log.save?.enable) minimal.basic.log.save = src.basic.log.save

    // 保留的插件键名
    const pluginKeys = ['database', 'server', 'webui']

    const keepAlways = [
        'record_message',
        'scheduler',
        'echo',
        'inspect',
        'auto_reload',
        'commands',
        'help',
        'database',
        'server',
        'webui',
    ]

    // 处理带前缀的插件
    const prefixMap: Record<string, string> = {
        record_message: '.',
        scheduler: '.',
        echo: '::',
        inspect: '::',
        auto_reload: '::',
        commands: '.',
        help: '::',
    }

    for (const name of keepAlways) {
        const prefix = prefixMap[name] ?? ''
        const enabled = pluginEnable[name as keyof typeof pluginEnable] ?? true
        const key = enabled ? `${prefix}${name}` : `~${name}`
        minimal.plugins[key] = src.plugins[name] ?? {}
    }

    // 其余插件直接按原名塞进去
    for (const k of pluginKeys) {
        if (k in src.plugins) minimal.plugins[k] = src.plugins[k]
    }

    if (src.plugins.$files) minimal.plugins.$files = src.plugins.$files
    if (src.plugins.$prelude) minimal.plugins.$prelude = src.plugins.$prelude

    try {
        await saveConfig(minimal)
        ElMessage.success('已保存')
    } catch (error) {
        console.error('保存失败', error)
        ElMessage.error('保存失败')
    }
}
</script>

<template>
    <div class="page">
        <el-card shadow="never" class="card">
            <template #header>
                <h1>系统设置</h1>
                <p>一站式管理 Entari WebUI 与后端参数</p>
            </template>

            <section>
                <h2>基础配置:</h2>
                <el-form label-width="120px" style="max-width:480px">
                    <el-form-item label="类型">
                        <el-select v-model="settings.basic.network[0].type" placeholder="选择网络类型">
                            <el-option label="ws" value="ws" />
                            <el-option label="websocket" value="websocket" />
                            <el-option label="wh" value="wh" />
                            <el-option label="webhook" value="webhook" />
                        </el-select>
                    </el-form-item>
                    <el-form-item label="服务器地址">
                        <el-input v-model="settings.basic.network[0].host" placeholder="satori 服务器地址" />
                    </el-form-item>
                    <el-form-item label="端口">
                        <el-input-number v-model="settings.basic.network[0].port" :min="1" :max="65535" />
                    </el-form-item>
                    <el-form-item label="路径">
                        <el-input v-model="settings.basic.network[0].path" placeholder="satori 服务器路径(默认为空)" />
                    </el-form-item>
                    <el-form-item label="token">
                        <el-input v-model="settings.basic.network[0].token" placeholder="账号配置文件的token" />
                    </el-form-item>
                    <el-form-item label="忽略自身消息">
                        <el-switch v-model="settings.basic.ignore_self_message" />
                    </el-form-item>
                    <el-form-item label="日志等级">
                        <el-select v-model="settings.basic.log.level" placeholder="选择日志等级" style="width:240px">
                            <el-option label="DEBUG" value="DEBUG" />
                            <el-option label="INFO" value="INFO" />
                            <el-option label="WARN" value="WARN" />
                            <el-option label="ERROR" value="ERROR" />
                        </el-select>
                    </el-form-item>
                    <el-form-item label="指令前缀">
                        <el-select v-model="settings.basic.prefix" multiple allow-create filterable
                            placeholder="可留空，默认为 /" style="width: 100%" />
                    </el-form-item>
                </el-form>
            </section>

            <section>
                <h2>插件配置:</h2>
                <el-form :model="settings.plugins" label-width="160px" style="max-width:600px">
                    <el-form-item label="插件搜索目录">
                        <el-input v-model="settings.plugins.$files" placeholder="多个目录用逗号分隔" />
                    </el-form-item>
                    <el-form-item label="预加载插件">
                        <el-input v-model="settings.plugins.$prelude" placeholder="多个插件用逗号分隔" />
                    </el-form-item>

                    <el-collapse>
                        <!-- 消息记录插件 -->
                        <el-collapse-item title="消息记录插件 (.record_message)">
                            <el-form-item label="启用">
                                <el-switch v-model="pluginEnable.record_message" />
                            </el-form-item>
                            <el-form-item label="记录发送消息">
                                <el-switch v-model="settings.plugins.record_message.record_send" />
                            </el-form-item>
                        </el-collapse-item>

                        <!-- 调度器插件 -->
                        <el-collapse-item title="调度器插件 (.scheduler)">
                            <el-form-item label="启用">
                                <el-switch v-model="pluginEnable.scheduler" />
                            </el-form-item>
                        </el-collapse-item>

                        <!-- 回声插件 -->
                        <el-collapse-item title="回声插件 (::echo)">
                            <el-form-item label="启用">
                                <el-switch v-model="pluginEnable.echo" />
                            </el-form-item>
                        </el-collapse-item>

                        <!-- 调试插件 -->
                        <el-collapse-item title="调试插件 (::inspect)">
                            <el-form-item label="启用">
                                <el-switch v-model="pluginEnable.inspect" />
                            </el-form-item>
                        </el-collapse-item>

                        <!-- 自动重载插件 -->
                        <el-collapse-item title="自动重载插件 (::auto_reload)">
                            <el-form-item label="启用">
                                <el-switch v-model="pluginEnable.auto_reload" />
                            </el-form-item>
                            <el-form-item label="监听目录">
                                <el-input v-model="settings.plugins.auto_reload.watch_dirs" placeholder="多个目录用逗号分隔" />
                            </el-form-item>
                            <el-form-item label="监听配置文件">
                                <el-switch v-model="settings.plugins.auto_reload.watch_config" />
                            </el-form-item>
                        </el-collapse-item>

                        <!-- 指令插件 -->
                        <el-collapse-item title="指令插件配置 (.commands)">
                            <el-form-item label="需要@机器人">
                                <el-switch v-model="settings.plugins.commands.need_notice_me" />
                            </el-form-item>
                            <el-form-item label="需要回复机器人">
                                <el-switch v-model="settings.plugins.commands.need_reply_me" />
                            </el-form-item>
                            <el-form-item label="使用配置前缀">
                                <el-switch v-model="settings.plugins.commands.use_config_prefix" />
                            </el-form-item>
                        </el-collapse-item>

                        <!-- 帮助插件 -->
                        <el-collapse-item title="帮助插件 (::help)">
                            <el-form-item label="帮助指令">
                                <el-input v-model="settings.plugins.help.help_command" placeholder="默认为 help" />
                            </el-form-item>
                            <el-form-item label="指令别名">
                                <el-input v-model="settings.plugins.help.help_alias"
                                    placeholder='多个别名用逗号分隔，如: "帮助","命令帮助"' />
                            </el-form-item>
                            <el-form-item label="每页数量">
                                <el-input-number v-model="settings.plugins.help.page_size" :min="1" />
                            </el-form-item>
                        </el-collapse-item>
                    </el-collapse>
                </el-form>

                <el-button class="save" @click="save" type="primary">保存配置</el-button>
            </section>
        </el-card>
    </div>
</template>

<style scoped>
.page {
    width: auto;
    padding: 24px;
    background: var(--set-page-bg);
}

.card {
    margin: 0 auto;
    background: var(--set-card-bg);
    border: 1px solid var(--set-card-border);
    box-shadow: 0 4px 12px var(--set-card-shadow);
}

h1 {
    margin: 0;
    font-size: 24px;
    color: var(--set-header-text);
    transition: color 0.3s;
}

h2 {
    margin: 24px 0 12px;
    font-size: 18px;
    color: var(--set-subheader-text);
    transition: color 0.3s;
}

section {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--set-divider);
    transition: border-color 0.3s;
}

:deep(.el-input__inner),
:deep(.el-textarea__inner),
:deep(.el-select .el-input__inner),
:deep(.el-input-number__inner) {
    background: var(--set-input-bg);
    border-color: var(--set-input-border);
    color: var(--set-input-text);
}

:deep(.el-input__inner::placeholder),
:deep(.el-textarea__inner::placeholder) {
    color: var(--set-input-placeholder);
}

:deep(.el-collapse-item__header) {
    padding-left: 62px;
    border-bottom: none;
    background: transparent;
    color: var(--set-collapse-item-title);
    font-size: 14px;
}

:deep(.el-collapse-item__content) {
    background: var(--set-card-bg);
    color: var(--set-input-text);
}

:deep(.el-collapse) {
    border: none;
    background: transparent;
}

:deep(.el-collapse-item__wrap) {
    border: none;
}

.save {
    margin-top: 20px;
}
</style>