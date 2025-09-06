<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import AnsiToHtml from 'ansi-to-html'

function cssVar(name: string): string {
    return getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim()
}

const logs = ref<string[]>([])
const logContainer = ref<HTMLDivElement>()
const socket = ref<WebSocket | null>(null)
const isConnected = ref(false)
const isAutoScroll = ref(true)
const ansi = new AnsiToHtml({
    escapeXML: true,
    colors: {
        0: cssVar('--log-ansi-black'), // 黑
        1: cssVar('--log-ansi-red'), // 红
        2: cssVar('--log-ansi-green'), // 绿
        3: cssVar('--log-ansi-yellow'), // 黄
        4: cssVar('--log-ansi-blue'), // 蓝
        5: cssVar('--log-ansi-magenta'), // 紫
        6: cssVar('--log-ansi-cyan'), // 青
        7: cssVar('--log-ansi-white'), // 白
    }
})

let shouldReconnect = true

function appendLog(line: string) {
    logs.value.push(line)
    // 自动滚动到底部
    if (isAutoScroll.value) {
        nextTick(() => {
            if (logContainer.value) {
                logContainer.value.scrollTop = logContainer.value.scrollHeight
            }
        })
    }
}

function handleScroll() {
    if (!logContainer.value) return;
    // 如果用户向上滚动超过 50px，就关闭自动滚动
    const { scrollTop, scrollHeight, clientHeight } = logContainer.value;
    isAutoScroll.value = scrollTop + clientHeight >= scrollHeight - 50;
}

function connectWebSocket() {
    const socketUrl = window.WS_PATH.baseURL || 'ws://127.0.0.1:5140/ws/log'

    shouldReconnect = true

    socket.value = new WebSocket(socketUrl)

    socket.value.onopen = () => {
        isConnected.value = true
        appendLog('=== 终端连接已建立 ===')
    }

    socket.value.onmessage = (event) => {
        const lines = event.data.split('\n')
        lines.forEach((line: string) => {
            if (line.trim()) {
                appendLog(line)
            }
        })
    }

    socket.value.onerror = (error) => {
        console.error('WebSocket错误:', error)
        appendLog('!!! 连接发生错误')
    }

    socket.value.onclose = () => {
        isConnected.value = false
        appendLog('=== 终端连接已关闭 ===')
        if (shouldReconnect) {
            setTimeout(connectWebSocket, 5000)
        }
    }
}

function clearLogs() {
    logs.value = []
}

function reconnect() {
    if (socket.value) {
        socket.value.close()
    }
    connectWebSocket()
}

function toggleAutoScroll() {
    isAutoScroll.value = !isAutoScroll.value
    if (isAutoScroll.value && logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
}

onMounted(() => {
    connectWebSocket()
})

onUnmounted(() => {
    if (socket.value) {
        socket.value.close()
    }
})
</script>

<template>
    <div class="main-page">
        <div class="console-page">
            <div class="header">
                <p>运行日志</p>
                <div class="actions">
                    <el-tag :type="isConnected ? 'success' : 'danger'">
                        {{ isConnected ? '已连接' : '已断开' }}
                    </el-tag>

                    <el-button size="small" plain :type="isAutoScroll ? 'primary' : ''" @click="toggleAutoScroll">
                        {{ isAutoScroll ? '自动滚动开启' : '自动滚动关闭' }}
                    </el-button>

                    <el-button size="small" @click="clearLogs">清空日志</el-button>
                    <el-button size="small" type="primary" @click="reconnect">重新连接</el-button>
                </div>
            </div>

            <div ref="logContainer" class="log-panel" @scroll="handleScroll">
                <div v-for="(line, index) in logs" :key="index" class="log-line" v-html="ansi.toHtml(line)" />
                <div v-if="logs.length === 0" class="empty-log">暂无日志数据</div>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.main-page {
    margin: 30px;
    width: auto;
    height: 85vh;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background: var(--log-header-bg);
    border-bottom: 1px solid var(--log-header-border);
    transition: background 0.3s, border-color 0.3s;

    p {
        color: var(--log-header-text);
        font-family: 'Microsoft YaHei', sans-serif;
        font-size: 16px;
        font-weight: bold;
        margin: 0;
        transition: color 0.3s;
    }

    .actions {
        display: flex;
        gap: 10px;
        align-items: center;
    }

    .el-button {
        height: 32px;
        font-size: 12px;
    }
}

.console-page {
    display: flex;
    flex-direction: column;
    height: 85vh;
    background: var(--log-bg);
    color: var(--log-text);
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.4;
    border-radius: 8px;
    box-shadow: 0 2px 12px var(--el-shadow);
    overflow: hidden;
    transition: background 0.3s, color 0.3s, box-shadow 0.3s;
}

.log-panel {
    flex: 1;
    padding: 12px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    color: var(--log-line-text);
    transition: color 0.3s;

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

.log-line {
    margin-bottom: 4px;
    line-height: 1.5;
}

.empty-log {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: var(--log-empty);
    font-style: italic;
    transition: color 0.3s;
}
</style>