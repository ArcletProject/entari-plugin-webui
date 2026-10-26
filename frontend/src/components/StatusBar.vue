<template>
  <div class="status-bar">
    <el-popover
      placement="top-start"
      :width="320"
      trigger="hover"
      popper-class="status-bar-popover"
    >
      <template #reference>
        <span class="status-bar-version">Entari v{{ system.entari_version || "…" }}</span>
      </template>
      <div class="info-list">
        <div class="info-row">
          <span class="info-label">{{ t("statusBar.system") }}</span>
          <span class="info-value">{{ system.system || "-" }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ t("statusBar.cpu") }}</span>
          <span class="info-value">{{ cpuText }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ t("statusBar.python") }}</span>
          <span class="info-value">{{ system.python || "-" }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ t("statusBar.entariVersion") }}</span>
          <span class="info-value">{{ system.entari_version ? `v${system.entari_version}` : "-" }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ t("statusBar.webuiVersion") }}</span>
          <span class="info-value">{{ system.webui_version ? `v${system.webui_version}` : "-" }}</span>
        </div>
      </div>
    </el-popover>

    <div class="spacer" />

    <el-popover
      placement="top-end"
      :width="360"
      trigger="hover"
      popper-class="status-bar-popover"
    >
      <template #reference>
        <span class="status-bar-accounts">
          <span class="lights">
            <span
              v-for="a in accounts"
              :key="accountKey(a)"
              class="light"
              :class="statusClass(a.status)"
              :title="`${a.name} · ${statusLabel(a.status)}`"
            />
            <span
              v-if="!accounts.length"
              class="light is-unknown"
              :title="t('statusBar.noAccounts')"
            />
          </span>
          <span class="rates">
            ↑ {{ summary.sent_per_min }}/min
            <span class="rate-gap" />
            ↓ {{ summary.received_per_min }}/min
          </span>
        </span>
      </template>

      <div
        v-if="!accounts.length"
        class="empty"
      >
        {{ t("statusBar.noAccounts") }}
      </div>
      <div
        v-else
        class="account-list"
      >
        <div
          v-for="a in accounts"
          :key="accountKey(a)"
          class="account-row"
        >
          <el-avatar
            :size="34"
            :src="a.avatar || undefined"
          >
            {{ initial(a.name) }}
          </el-avatar>
          <div class="account-meta">
            <span class="account-name">{{ a.name }}</span>
            <span class="account-sub">{{ a.platform }} · {{ a.adapter }} · {{ statusLabel(a.status) }}</span>
          </div>
          <span class="account-rates">
            ↑ {{ a.sent_per_min }}/min<br>
            ↓ {{ a.received_per_min }}/min
          </span>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";

interface SystemInfo {
  system?: string;
  cpu?: string;
  cpu_count?: number;
  python?: string;
  entari_version?: string;
  webui_version?: string;
}

interface AccountInfo {
  self_id: string;
  name: string;
  avatar: string | null;
  platform: string;
  adapter: string;
  status: string;
  sent_per_min: number;
  received_per_min: number;
}

interface AccountSummary {
  total: number;
  online: number;
  sent_per_min: number;
  received_per_min: number;
}

const { t } = useI18n();

const system = ref<SystemInfo>({});
const accounts = ref<AccountInfo[]>([]);
const summary = ref<AccountSummary>({ total: 0, online: 0, sent_per_min: 0, received_per_min: 0 });
let timer: number | undefined;

const cpuText = computed(() => {
  if (!system.value.cpu) return "-";
  return system.value.cpu_count ? `${system.value.cpu} (${system.value.cpu_count} 核)` : system.value.cpu;
});

const STATUS_CLASS: Record<string, string> = {
  online: "is-online",
  connect: "is-connecting",
  reconnect: "is-connecting",
  disconnect: "is-danger",
  offline: "is-offline",
};

function statusClass(status: string): string {
  return STATUS_CLASS[status] ?? "is-unknown";
}

function statusLabel(status: string): string {
  const key = `statusBar.status.${status}`;
  const label = t(key);
  return label === key ? status : label;
}

function accountKey(account: AccountInfo): string {
  return `${account.platform}:${account.self_id}:${account.adapter}`;
}

function initial(name: string): string {
  return name?.trim().charAt(0).toUpperCase() || "?";
}

async function refreshAccounts(): Promise<void> {
  try {
    const r = await api.get("/api/accounts");
    accounts.value = r.data.accounts ?? [];
    summary.value = r.data.summary ?? { total: 0, online: 0, sent_per_min: 0, received_per_min: 0 };
  } catch {
    // 后端暂时不可达时保留上一次数据
  }
}

onMounted(async () => {
  try {
    const r = await api.get("/api/system");
    system.value = r.data;
  } catch {
    // 版本信息加载失败不影响状态栏
  }
  await refreshAccounts();
  timer = window.setInterval(refreshAccounts, 5000);
});

onUnmounted(() => {
  if (timer !== undefined) window.clearInterval(timer);
});
</script>

<style scoped>
.status-bar {
  height: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  user-select: none;
}
.spacer { flex: 1; }
.status-bar-version {
  padding: 2px 6px;
  border-radius: 4px;
  cursor: default;
}
.status-bar-version:hover,
.status-bar-accounts:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}
.status-bar-accounts {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: default;
}
.lights {
  display: flex;
  align-items: center;
  gap: 4px;
}
.light {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--el-text-color-disabled);
  box-shadow: 0 0 0 1px var(--el-border-color-lighter);
}
.light.is-online { background: var(--el-color-success); }
.light.is-connecting { background: var(--el-color-warning); }
.light.is-danger { background: var(--el-color-danger); }
.light.is-offline { background: var(--el-color-danger); }
.light.is-unknown { background: var(--el-text-color-disabled); }
.rates {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.rate-gap { display: inline-block; width: 6px; }
.info-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.info-label { color: var(--el-text-color-secondary); white-space: nowrap; }
.info-value { text-align: right; word-break: break-word; }
.empty {
  padding: 8px 4px;
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.account-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.account-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.account-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}
.account-name {
  font-size: 13px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.account-sub {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.account-rates {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
  text-align: right;
  white-space: nowrap;
}
</style>
