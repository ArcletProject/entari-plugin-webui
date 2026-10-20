import assert from "node:assert/strict";
import test from "node:test";
import { mergePluginSources } from "../src/utils/plugin-list.ts";

test("合并已加载、已卸载与内置插件并去重", () => {
  const loaded = [
    { id: "demo", name: "Demo", type: "local", parent: null, enabled: true, is_static: false, configurable: true },
    { id: "arclet.entari.builtins.echo", name: "Echo", type: "built-in", parent: null, enabled: true, is_static: false, configurable: false },
  ];
  const unloaded = [
    { key: "old", id: "old", name: "Old", display_key: "?old", state: "unloaded", config: {} },
    { key: "?::pipe", id: "arclet.entari.builtins.pipe", name: "::pipe", display_key: "??::pipe", state: "unloaded", config: {} },
  ];
  const builtins = [
    { name: "echo", id: "arclet.entari.builtins.echo", key: "::echo", title: "Echo", description: "d", loaded: true, enabled: true, static: false },
    { name: "pipe", id: "arclet.entari.builtins.pipe", key: "::pipe", title: "Pipe", description: "p", loaded: false, enabled: false, static: false },
  ];
  const out = mergePluginSources(loaded, unloaded, builtins);
  assert.deepEqual(out.map((p) => p.uid).sort(), ["demo", "?old", "?::pipe", "arclet.entari.builtins.echo"].sort());
  const pipe = out.find((p) => p.uid === "?::pipe")!;
  assert.equal(pipe.builtin_title, "Pipe");
  assert.equal(pipe.unloaded, true);
});
