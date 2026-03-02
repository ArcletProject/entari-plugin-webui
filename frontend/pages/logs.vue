<template>
  <div class="logs-page">
    <n-card title="实时日志">
      <template #header-extra>
        <n-space>
          <n-tag :type="connected ? 'success' : 'error'">
            {{ connected ? '已连接' : '未连接' }}
          </n-tag>
          <n-button v-if="!connected" size="small" @click="connect">
            重新连接
          </n-button>
          <n-button size="small" @click="clearLogs">
            清空
          </n-button>
          <n-switch v-model:value="autoScroll">
            <template #checked>自动滚动</template>
            <template #unchecked>自动滚动</template>
          </n-switch>
        </n-space>
      </template>

      <div ref="logContainer" class="log-container">
        <pre class="log-content" v-html="logHtml"></pre>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import AnsiToHtml from 'ansi-to-html'

const ansiConverter = new AnsiToHtml({
  fg: '#aaa',
  bg: 'transparent',
  newline: true,
  escapeXML: true,
})

const logContainer = ref<HTMLElement | null>(null)
const logs = ref<string[]>([])
const autoScroll = ref(true)

// WebSocket 连接
const { connected, connect, disconnect } = useWebSocketConnection('/ws/logs', {
  onMessage: (data) => {
    if (data.type === 'history' || data.type === 'log') {
      logs.value.push(data.data)
      // 限制日志行数
      if (logs.value.length > 1000) {
        logs.value = logs.value.slice(-500)
      }
      // 自动滚动
      if (autoScroll.value) {
        nextTick(() => {
          scrollToBottom()
        })
      }
    }
  },
})

// 日志 HTML
const logHtml = computed(() => {
  return logs.value.map(log => ansiConverter.toHtml(log)).join('')
})

// 滚动到底部
const scrollToBottom = () => {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

// 清空日志
const clearLogs = () => {
  logs.value = []
}

// 初始化
onMounted(() => {
  connect()
})

onUnmounted(() => {
  disconnect()
})
</script>

<style scoped>
.logs-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logs-page :deep(.n-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logs-page :deep(.n-card__content) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.log-container {
  height: 100%;
  overflow: auto;
  background: #1e1e1e;
  border-radius: 4px;
}

.log-content {
  margin: 0;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
