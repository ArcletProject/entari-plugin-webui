import assert from "node:assert/strict";
import test from "node:test";

import { resolveRef } from "../src/components/schema-form/resolve-ref.ts";

const root = {
  $defs: {
    RootDef: {
      type: "object",
      title: "RootDef",
      properties: { a: { type: "integer" } },
    },
  },
  properties: {
    ".child": {
      $defs: {
        ChildInner: {
          type: "object",
          title: "ChildInner",
          properties: { value: { type: "string" } },
        },
      },
    },
    "a/b": { type: "string" },
    "c~d": { type: "number" },
  },
};

test("resolves a root-level $defs reference", () => {
  const out = resolveRef({ $ref: "#/$defs/RootDef" }, root);
  assert.equal(out.title, "RootDef");
  assert.deepEqual(out.properties, { a: { type: "integer" } });
});

test("resolves a nested sub-plugin $defs reference", () => {
  const out = resolveRef({ $ref: "#/properties/.child/$defs/ChildInner" }, root);
  assert.equal(out.title, "ChildInner");
  assert.deepEqual(out.properties, { value: { type: "string" } });
});

test("keeps title and description from the referencing schema", () => {
  const out = resolveRef(
    { $ref: "#/$defs/RootDef", title: "自定义", description: "说明" },
    root,
  );
  assert.equal(out.title, "自定义");
  assert.equal(out.description, "说明");
});

test("unescapes JSON Pointer tokens", () => {
  assert.equal(resolveRef({ $ref: "#/properties/a~1b" }, root).type, "string");
  assert.equal(resolveRef({ $ref: "#/properties/c~0d" }, root).type, "number");
});

test("returns the schema unchanged when the reference cannot be resolved", () => {
  const schema = { $ref: "#/$defs/Missing" };
  assert.equal(resolveRef(schema, root), schema);
});
