import { ref } from "vue";
import api from "@/api/client";

export type HealthState = "online" | "reconnecting" | "offline";
const state = ref<HealthState>("online");
let miss = 0;
let timer: number | null = null;
const recoveredCbs = new Set<() => void>();

async function probe(): Promise<boolean> {
  try {
    await api.get("/api/health", { timeout: 2000 });
    return true;
  } catch {
    return false;
  }
}

function set(next: HealthState) {
  if (state.value === next) return;
  state.value = next;
  if (next === "online") {
    recoveredCbs.forEach((cb) => cb());
  }
}

export function useBackendHealth() {
  async function start() {
    if (timer) return;
    timer = window.setInterval(tick, 5000);
    await tick();
  }
  async function tick() {
    const ok = await probe();
    if (ok) { miss = 0; set("online"); return; }
    miss += 1;
    if (miss === 1) set("reconnecting");
    if (miss >= 3) set("offline");
  }
  async function reconnectNow() {
    miss = 0; set("online");
    await tick();
  }
  function onRecovered(cb: () => void) { recoveredCbs.add(cb); return () => recoveredCbs.delete(cb); }
  return { state, start, reconnectNow, onRecovered };
}
