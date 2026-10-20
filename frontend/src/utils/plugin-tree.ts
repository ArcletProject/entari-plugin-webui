export type PluginDisplayMode = "top" | "configured" | "all";

export type PluginType = "rootless" | "built-in" | "local" | "common";

export interface PluginLike {
  id: string;
  name: string;
  type: PluginType;
  parent?: string | null;
  has_metadata?: boolean;
  has_config_schema?: boolean;
}

export interface PluginSearchTarget {
  id?: string | null;
  name?: string | null;
  key?: string | null;
  config_key?: string | null;
  display_key?: string | null;
  uid?: string | null;
  builtin_title?: string | null;
}

/** 名称、id、配置键等字段的共用模糊匹配；空白查询视为不过滤。 */
export function matchesPluginSearch(plugin: PluginSearchTarget, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return [plugin.name, plugin.id, plugin.key, plugin.config_key, plugin.display_key, plugin.uid, plugin.builtin_title]
    .filter((value): value is string => Boolean(value))
    .some((value) => value.toLowerCase().includes(q));
}

export interface PluginTreeNode<T extends PluginLike> {
  plugin: T;
  children: PluginTreeNode<T>[];
}

export interface FlatPluginTreeNode<T extends PluginLike> {
  plugin: T;
  depth: number;
  hasChildren: boolean;
}

const PLUGIN_TYPES: PluginType[] = ["rootless", "built-in", "local", "common"];

export function isSubplugin(plugin: PluginLike): boolean {
  return Boolean(plugin.parent && plugin.parent !== plugin.id);
}

export function isSubpluginVisible(plugin: PluginLike, mode: PluginDisplayMode): boolean {
  if (!isSubplugin(plugin)) return true;
  // 根基础与内置插件及其子插件不受三态过滤影响。
  if (plugin.type === "rootless" || plugin.type === "built-in") return true;
  if (mode === "all") return true;
  if (mode === "top") return false;
  return Boolean(plugin.has_metadata || plugin.has_config_schema);
}

function createsParentCycle(plugin: PluginLike, byId: Map<string, PluginLike>): boolean {
  const seen = new Set<string>([plugin.id]);
  let parentId = plugin.parent;
  while (parentId) {
    if (seen.has(parentId)) return true;
    seen.add(parentId);
    const parent = byId.get(parentId);
    if (!parent) return false;
    parentId = parent.parent;
  }
  return false;
}

function sortNodes<T extends PluginLike>(nodes: PluginTreeNode<T>[]): void {
  nodes.sort((a, b) => {
    const byName = a.plugin.name.toLowerCase().localeCompare(b.plugin.name.toLowerCase());
    return byName || a.plugin.id.localeCompare(b.plugin.id);
  });
  for (const node of nodes) sortNodes(node.children);
}

export function buildPluginTree<T extends PluginLike>(plugins: T[]): Record<PluginType, PluginTreeNode<T>[]> {
  const groups = Object.fromEntries(PLUGIN_TYPES.map((type) => [type, [] as PluginTreeNode<T>[]])) as Record<
    PluginType,
    PluginTreeNode<T>[]
  >;
  const byId = new Map(plugins.map((plugin) => [plugin.id, plugin]));
  const nodes = new Map<string, PluginTreeNode<T>>();
  for (const plugin of plugins) {
    nodes.set(plugin.id, { plugin, children: [] });
  }
  for (const plugin of plugins) {
    const node = nodes.get(plugin.id)!;
    const parentId = plugin.parent;
    const parent = parentId && parentId !== plugin.id ? nodes.get(parentId) : undefined;
    if (parent && !createsParentCycle(plugin, byId)) {
      parent.children.push(node);
    } else {
      groups[plugin.type].push(node);
    }
  }
  for (const type of PLUGIN_TYPES) sortNodes(groups[type]);
  return groups;
}

function collectPinnedChain<T extends PluginLike>(nodes: PluginTreeNode<T>[], pinnedId: string): Set<string> {
  const chain = new Set<string>();
  function find(node: PluginTreeNode<T>): boolean {
    chain.add(node.plugin.id);
    if (node.plugin.id === pinnedId) return true;
    for (const child of node.children) {
      if (find(child)) return true;
    }
    chain.delete(node.plugin.id);
    return false;
  }
  for (const node of nodes) {
    if (find(node)) return chain;
  }
  return new Set<string>();
}

export function filterPluginTree<T extends PluginLike>(
  groups: Record<PluginType, PluginTreeNode<T>[]>,
  mode: PluginDisplayMode,
  pinnedId?: string,
): Record<PluginType, PluginTreeNode<T>[]> {
  const allNodes = PLUGIN_TYPES.flatMap((type) => groups[type]);
  const pinnedChain = pinnedId ? collectPinnedChain(allNodes, pinnedId) : new Set<string>();

  function filterNodes(nodes: PluginTreeNode<T>[]): PluginTreeNode<T>[] {
    const kept: PluginTreeNode<T>[] = [];
    for (const node of nodes) {
      const children = filterNodes(node.children);
      const keepSelf = isSubpluginVisible(node.plugin, mode) || pinnedChain.has(node.plugin.id);
      if (keepSelf || children.length > 0) {
        kept.push({ plugin: node.plugin, children });
      }
    }
    return kept;
  }

  return Object.fromEntries(
    PLUGIN_TYPES.map((type) => [type, filterNodes(groups[type])]),
  ) as Record<PluginType, PluginTreeNode<T>[]>;
}

export function flattenPluginTree<T extends PluginLike>(
  nodes: PluginTreeNode<T>[],
  isExpanded: (id: string) => boolean,
): FlatPluginTreeNode<T>[] {
  const result: FlatPluginTreeNode<T>[] = [];
  function walk(current: PluginTreeNode<T>[], depth: number): void {
    for (const node of current) {
      const hasChildren = node.children.length > 0;
      result.push({ plugin: node.plugin, depth, hasChildren });
      if (hasChildren && isExpanded(node.plugin.id)) walk(node.children, depth + 1);
    }
  }
  walk(nodes, 0);
  return result;
}
