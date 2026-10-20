import type { ManagedPlugin, PluginState } from "../stores/plugins";

type Source = Record<string, unknown>;

const TYPES = new Set(["rootless", "built-in", "local", "common"]);
const STATES = new Set<PluginState>(["enabled", "disabled", "unavailable", "unloaded"]);

function str(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : value == null ? fallback : String(value);
}

function bool(value: unknown): boolean {
  return value === true;
}

function normalizeKey(key: string): string {
  return key.replace(/^\?/, "");
}

function pluginType(value: unknown): ManagedPlugin["type"] {
  return typeof value === "string" && TYPES.has(value) ? (value as ManagedPlugin["type"]) : "common";
}

function pluginState(value: unknown, enabled: boolean): PluginState {
  return typeof value === "string" && STATES.has(value as PluginState)
    ? (value as PluginState)
    : enabled
      ? "enabled"
      : "unavailable";
}

function parentOf(value: unknown): string | null {
  return typeof value === "string" && value ? value : null;
}

function loadedPlugin(raw: Source): ManagedPlugin {
  const id = str(raw.id ?? raw.uid);
  const enabled = bool(raw.enabled);
  return {
    id,
    uid: id,
    key: str(raw.key ?? raw.config_key) || undefined,
    name: str(raw.name, id),
    description: str(raw.description) || undefined,
    version: str(raw.version) || undefined,
    type: pluginType(raw.type),
    enabled,
    is_static: bool(raw.is_static),
    configurable: bool(raw.configurable),
    parent: parentOf(raw.parent),
    has_metadata: bool(raw.has_metadata),
    has_config_schema: bool(raw.has_config_schema),
    can_unload: bool(raw.can_unload),
    state: pluginState(raw.state, enabled),
    disable_expr: typeof raw.disable_expr === "string" ? raw.disable_expr : null,
    parent_enabled: typeof raw.parent_enabled === "boolean" ? raw.parent_enabled : null,
    unloaded: false,
    market: (raw.market as ManagedPlugin["market"]) ?? null,
  };
}

function unloadedPlugin(raw: Source, builtin?: Source): ManagedPlugin {
  const key = normalizeKey(str(raw.key ?? raw.id));
  const name = str(raw.name, key);
  return {
    id: raw.id ? str(raw.id) : null,
    uid: `?${key}`,
    key,
    display_key: `?${key}`,
    name: str(builtin?.title, name),
    description: str(raw.description ?? builtin?.description) || undefined,
    version: str(raw.version) || undefined,
    type: builtin ? "built-in" : pluginType(raw.type),
    enabled: false,
    is_static: bool(builtin?.static ?? raw.is_static),
    configurable: false,
    parent: null,
    has_metadata: false,
    has_config_schema: false,
    can_unload: false,
    state: "unloaded",
    disable_expr: null,
    parent_enabled: null,
    unloaded: true,
    builtin_name: builtin ? str(builtin.name) : undefined,
    builtin_title: builtin ? str(builtin.title) : undefined,
    builtin_description: builtin ? str(builtin.description) : undefined,
  };
}

function availableBuiltin(raw: Source): ManagedPlugin {
  const name = str(raw.name);
  const id = str(raw.id);
  return {
    id,
    uid: `::${name}`,
    key: str(raw.key ?? `::${name}`),
    name: str(raw.title, name),
    description: str(raw.description) || undefined,
    type: "built-in",
    enabled: false,
    is_static: bool(raw.static),
    configurable: false,
    parent: null,
    has_metadata: false,
    has_config_schema: false,
    can_unload: false,
    state: "unavailable",
    disable_expr: null,
    parent_enabled: null,
    unloaded: false,
    builtin_name: name,
    builtin_title: str(raw.title, name),
    builtin_description: str(raw.description) || undefined,
  };
}

export function mergePluginSources(loaded: Source[], unloaded: Source[], builtins: Source[]): ManagedPlugin[] {
  const loadedPlugins = loaded.map(loadedPlugin).filter((p) => p.id);
  const loadedIds = new Set(loadedPlugins.map((p) => p.id));
  const loadedKeys = new Set(
    loadedPlugins.flatMap((p) => [p.key, p.id].filter((k): k is string => !!k).map(normalizeKey)),
  );

  const builtinByKey = new Map<string, Source>();
  for (const builtin of builtins) {
    builtinByKey.set(normalizeKey(str(builtin.key ?? `::${str(builtin.name)}`)), builtin);
  }

  const unloadedPlugins = unloaded
    .map((raw) => {
      const key = normalizeKey(str(raw.key ?? raw.id));
      return unloadedPlugin(raw, builtinByKey.get(key));
    })
    .filter((p) => p.key);
  const unloadedKeys = new Set(unloadedPlugins.map((p) => normalizeKey(p.key ?? "")));

  const available = builtins
    .filter((builtin) => {
      const key = normalizeKey(str(builtin.key ?? `::${str(builtin.name)}`));
      return !loadedKeys.has(key) && !unloadedKeys.has(key) && !loadedIds.has(str(builtin.id));
    })
    .map(availableBuiltin);

  const byUid = new Map<string, ManagedPlugin>();
  for (const plugin of [...loadedPlugins, ...unloadedPlugins, ...available]) {
    byUid.set(plugin.uid, plugin);
  }

  return [...byUid.values()].sort((a, b) => {
    const byName = a.name.toLowerCase().localeCompare(b.name.toLowerCase());
    return byName || a.uid.localeCompare(b.uid);
  });
}
