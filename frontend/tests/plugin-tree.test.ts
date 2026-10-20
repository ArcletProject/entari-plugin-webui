import assert from "node:assert/strict";
import test from "node:test";
import {
  buildPluginTree,
  filterPluginTree,
  flattenPluginTree,
  isSubpluginVisible,
  matchesPluginSearch,
} from "../src/utils/plugin-tree.ts";

const plugins = [
  { id: "root", name: "Root", type: "rootless" as const, parent: null },
  { id: "root.child", name: "RootChild", type: "rootless" as const, parent: "root" },
  { id: "builtin", name: "Builtin", type: "built-in" as const, parent: null },
  { id: "parent", name: "Parent", type: "local" as const, parent: null },
  { id: "parent.meta", name: "Meta", type: "local" as const, parent: "parent", has_metadata: true },
  { id: "parent.schema", name: "Schema", type: "local" as const, parent: "parent", has_config_schema: true },
  { id: "parent.bare", name: "Bare", type: "local" as const, parent: "parent" },
  { id: "parent.bare.deep", name: "Deep", type: "local" as const, parent: "parent.bare", has_metadata: true },
];

test("configured 模式只显示有元数据或 schema 的子插件，并保留祖先", () => {
  const groups = filterPluginTree(buildPluginTree(plugins), "configured");
  const parent = groups.local.find((n) => n.plugin.id === "parent")!;
  assert.deepEqual(parent.children.map((n) => n.plugin.id), ["parent.bare", "parent.meta", "parent.schema"]);
  assert.deepEqual(parent.children[0].children.map((n) => n.plugin.id), ["parent.bare.deep"]);
});

test("top 模式隐藏普通子插件，但根基础与内置子插件仍显示", () => {
  const groups = filterPluginTree(buildPluginTree(plugins), "top");
  assert.deepEqual(groups.local[0].children, []);
  assert.deepEqual(groups.rootless[0].children.map((n) => n.plugin.id), ["root.child"]);
});

test("pinned 子插件即使被过滤也保留", () => {
  const groups = filterPluginTree(buildPluginTree(plugins), "top", "parent.bare");
  const parent = groups.local.find((n) => n.plugin.id === "parent")!;
  assert.deepEqual(parent.children.map((n) => n.plugin.id), ["parent.bare"]);
});

test("flatten 保留深度并跳过折叠子节点", () => {
  const groups = buildPluginTree(plugins);
  const flat = flattenPluginTree(groups.local, (id) => id !== "parent.bare");
  assert.equal(flat[0].depth, 0);
  assert.ok(flat.some((n) => n.plugin.id === "parent.meta" && n.depth === 1));
  assert.ok(!flat.some((n) => n.plugin.id === "parent.bare.deep"));
});

test("搜索匹配名称、id 与配置键", () => {
  const plugin = {
    id: "entari_plugin_weather",
    name: "天气查询",
    type: "common" as const,
    config_key: "weather",
  };
  assert.equal(matchesPluginSearch(plugin, "天气"), true);
  assert.equal(matchesPluginSearch(plugin, "ENTARI_PLUGIN"), true);
  assert.equal(matchesPluginSearch(plugin, "weather"), true);
  assert.equal(matchesPluginSearch(plugin, "missing"), false);
  assert.equal(matchesPluginSearch(plugin, "  "), true);
});

test("isSubpluginVisible 按模式判断", () => {
  const bare = plugins[6];
  assert.equal(isSubpluginVisible(bare, "all"), true);
  assert.equal(isSubpluginVisible(bare, "configured"), false);
  assert.equal(isSubpluginVisible(plugins[4], "configured"), true);
});
